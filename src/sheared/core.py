# vim:nowrap:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby <sune@mel.interspace.dk>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import os
import sys
from itertools import chain
from time import time
from py.magic import greenlet
from select import select
from select import error as SelectError
from socket import socket, SOL_SOCKET, SO_ERROR, SO_REUSEADDR
from socket import error as SocketError
from fcntl import fcntl, F_SETFL
from errno import EINPROGRESS
from heapq import heappush, heappop

from sheared.prelude import parse_address_uri, ReactorFile, ReactorSocket
from sheared.error import TimeoutError, ReactorExit

import logging
log = logging.getLogger(__name__)

# Obects used to identify why we switch back from the core-greenley
# to a user-greenlet.
EV_TIMEOUT = TimeoutError
EV_IO_READY = object()

class Reactor:
    def __init__(self):
        # State of reactor, is 'stopped', 'running' or 'stopping'
        self.state = 'stopped'
        # Mapping selected file descriptors to greenlets
        self.fd_greenlet = {}
        # File descriptors sets to select on
        self.reading, self.writing = [], []
        # heapq of sleeping processes
        self.sleepers = []
        
    # -*- Reactor control functions -*-
    def start(self, f):
        if not self.state == 'stopped':
            raise AssertionError, 'reactor not stopped'

        try:
            self.state = 'running'
            self.__bootstrap(f)
            self.__mainloop()
            self.__cleanup()
            self.state = 'stopped'
        except:
            self.state = 'b0rked'
            raise

    def stop(self):
        self.state = 'stopping'

    # -*- Greenlet control functions -*-
    def sleep(self, seconds):
        g = greenlet.getcurrent()
        heappush(self.sleepers, (time() + seconds, g))
        r = g.parent.switch()

    def spawn(self, function, args=(), kwargs={}):
        g = greenlet(function)
        heappush(self.sleepers, (0.0, g.parent))
        g.parent = g.parent.parent
        r = g.switch(*args, **kwargs)
        if not r is EV_TIMEOUT:
            raise AssertionError('sleeping greenlet awoken with %r' % r)

    # -*- I/O Convenience methods -*-
    def open(self, *args):
        f = open(*args)
        rf = ReactorFile(self, f.fileno())
        rf.file = f
        return rf

    def listen(self, factory, addr, backlog=5):
        domain, addr = parse_address_uri(addr)
        sock = socket(*domain)
        fcntl(sock.fileno(), F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        self.spawn(self.__accept, (factory, sock))

    def connect(self, addr, timeout=None):
        domain, addr = parse_address_uri(addr)
        sock = socket(*domain)
        fcntl(sock.fileno(), F_SETFL, os.O_NONBLOCK)

        try:
            sock.connect(addr)
        except SocketError, (eno, _):
            if not eno == EINPROGRESS:
                raise
        self.__wait_on_io(sock.fileno(), self.writing, timeout)
        
        err = sock.getsockopt(SOL_SOCKET, SO_ERROR)
        if err:
            raise SocketError, (err, os.strerror(err))

        return ReactorSocket(self, sock)

    def __accept(self, factory, sock):
        try:
            while 1:
                try:
                    self.__wait_on_io(sock.fileno(), self.reading, None)
                except ReactorExit:
                    break
                s, a = sock.accept()
                fcntl(s.fileno(), F_SETFL, os.O_NONBLOCK)
                t = ReactorSocket(self, s)
                self.spawn(factory, (t,))
            
        finally:
            try:
                sock.close()
            except:
                pass

    # -*- Internal reactor bookkeeping methods -*-
    def __bootstrap(self, f):
        g = greenlet(f)
        g.switch(self)

    def __mainloop(self):
        while 1:
            now = time()
            timeout = self.__wake_sleepers(now)
            if not timeout and not self.reading and not self.writing:
                break
            if not self.state == 'running':
                break
            self.__select(timeout)

    def __cleanup(self):
        err = ReactorExit('Reactor is shutting down')
        for fd in self.reading + self.writing:
            self.__notify_on_fd(fd, err)

        assert not (self.fd_greenlet or self.reading or self.writing)

    # -*- Internal I/O methods called in user greenlets -*-
    def _read(self, fd, max, timeout):
        self.__wait_on_io(fd, self.reading, timeout)
        return os.read(fd, max)
    def _write(self, fd, data, timeout):
        self.__wait_on_io(fd, self.writing, timeout)
        return os.write(fd, data)

    def __wait_on_io(self, fd, l, t):
        g = greenlet.getcurrent()
        self.fd_greenlet[fd] = g, l
        l.append(fd)
        if t is not None:
            heappush(self.sleepers, (t, g))
        r = g.parent.switch()

        if r is EV_IO_READY:
            return
        elif r is EV_TIMEOUT:
            self.__notify_on_fd(fd, TimeoutError())
        else:
            raise AssertionError('I/O-waiting greenlet awoken with %r' % r)

    # -*- Internal I/O methods called in reactor greenlet -*-
    def __wake_sleepers(self, now):
        while self.sleepers and self.sleepers[0][0] <= now:
            t, g = heappop(self.sleepers)
            if now - t > 3.0:
                log.info('... greenlet overslept.')
            g.switch(EV_TIMEOUT)
        if self.sleepers:
            return self.sleepers[0][0] - now
        else:
            return None

    def __select(self, timeout):
        try:
            r, w, e = select(self.reading, self.writing, [], timeout)
            for fd in chain(r, w, e):
                self.__notify_on_fd(fd)
        except SelectError:
            log.warn('Error waiting for I/O', exc_info=True)
            self.__flush_unselectables()

    def __notify_on_fd(self, fd, ev=EV_IO_READY):
        g, l = self.fd_greenlet.pop(fd)
        l.remove(fd)

        if g.dead:
            log.error('Greenlet waiting for IO in %d is dead')
        elif isinstance(ev, Exception):
            g.throw(ev)
        elif ev is not None:
            g.switch(ev)

    def __flush_unselectables(self):
        # Assume there is only one, if there are more, we'll just get called
        # more than once.
        try:
            for fd in self.reading:
                select([fd], [], [], 0.0)
            for fd in self.writing:
                select([], [fd], [], 0.0)
        except SelectError, err:
            self.__notify_on_fd(fd, err)
        
__all__ = ['Reactor']