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

from py.magic import greenlet

import os
import sys
import time
import select
import socket
import fcntl
import errno
from heapq import heappush, heappop

# dummy object for detecting dead greenlets
dummy = object()

def parse_address_uri(where):
    domain, address = where.split(':', 1)

    if domain == 'tcp':
        domain = socket.AF_INET, socket.SOCK_STREAM
        ip, port = address.split(':')
        if ip == '*':
            ip = ''
        try:
            port = int(port)
        except ValueError:
            port = socket.getservbyname(port, 'tcp')
        address = ip, port

    elif domain == 'unix':
        domain = socket.AF_UNIX, socket.SOCK_STREAM

    else:
        raise 'Unknown domain: %s' % domain

    return domain, address

class ReactorExit(Exception):
    pass

class ReactorFile:
    def __init__(self, reactor, fd): 
        self.reactor = reactor
        self.fd = fd

    def read(self, max=None):
        if max is None:
            data = ''
            while 1:
                d = self.reactor.read(self.fd, 8192)
                if d == '':
                    break
                data = data + d
            return data
        else:
            return self.reactor.read(self.fd, max)

    def write(self, data):
        while data:
            i = self.reactor.write(self.fd, data)
            data = data[i:]

    def close(self):
        os.close(self.fd)
        del self.reactor

class ReactorSocket(ReactorFile):
    def __init__(self, reactor, sock):
        self.reactor = reactor
        self.sock = sock
        self.fd = self.sock.fileno()

    def shutdown(self, how):
        self.sock.shutdown(how)

    def close(self):
        self.sock.close()
        del self.reactor
        del self.sock

class Reactor:
    def __init__(self):
        # state of reactor, is 'stopped', 'running' or 'stopping'
        self.state = 'stopped'
        # mapping selected file descriptors to greenlets
        self.fd_greenlet = {}
        # file descriptors sets to select on
        self.reading, self.writing = [], []
        # heapq of sleeping processes
        self.sleepers = []
        
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

    def sleep(self, seconds):
        g = greenlet.getcurrent()
        heappush(self.sleepers, (time.time() + seconds, g))
        result = g.parent.switch()
        if not result is dummy:
            raise result

    def spawn(self, function, args=(), kwargs={}):
        g = greenlet(function)
        heappush(self.sleepers, (0.0, g.parent))
        g.parent = g.parent.parent
        g.switch(*args, **kwargs)

    def read(self, fd, max):
        self.__wait_on_io(fd, self.reading)
        return os.read(fd, max)
    def write(self, fd, data):
        self.__wait_on_io(fd, self.writing)
        return os.write(fd, data)

    def listen(self, factory, addr, backlog=5):
        domain, addr = parse_address_uri(addr)
        sock = socket.socket(*domain)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        self.spawn(self.__accept, (factory, sock))

    def connect(self, addr):
        domain, addr = parse_address_uri(addr)
        sock = socket.socket(*domain)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)

        try:
            sock.connect(addr)
        except socket.error, (eno, _):
            if not eno == errno.EINPROGRESS:
                raise
        self.__wait_on_io(sock.fileno(), self.writing)
        
        err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            raise socket.error, (err, os.strerror(err))

        return ReactorSocket(self, sock)

    def __accept(self, factory, sock):
        try:
            while 1:
                try:
                    self.__wait_on_io(sock.fileno(), self.reading)
                except ReactorExit:
                    break
                s, a = sock.accept()
                fcntl.fcntl(s.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
                t = ReactorSocket(self, s)
                self.spawn(factory, (t,))
            
        finally:
            try:
                sock.close()
            except:
                pass

    def __wait_on_io(self, fd, list):
        g = greenlet.getcurrent()
        self.fd_greenlet[fd] = g
        list.append(fd)
        result = g.parent.switch()
        list.remove(fd)
        del self.fd_greenlet[fd]

        if not result is dummy:
            raise result

    def __bootstrap(self, f):
        g = greenlet(f)
        g.switch(self)

    def __mainloop(self):
        while 1:
            now = time.time()
            timeout = self.__wake_sleepers(now)
            if not timeout and not self.reading and not self.writing:
                break
            if not self.state == 'running':
                break
            self.__select(timeout)

    def __cleanup(self):
        # FIXME -- this code-path is untested
        for fd in self.reading + self.writing:
            g = self.fd_greenlet[fd]
            g.switch(ReactorExit('reactor is shutting down'))

        self.fd_greenlet = {}
        self.reading, self.writing = [], []

    def __wake_sleepers(self, now):
        while self.sleepers and self.sleepers[0][0] <= now:
            _, g = heappop(self.sleepers)
            g.switch(dummy)
        if self.sleepers:
            return self.sleepers[0][0] - now
        else:
            return None

    def __select(self, timeout):
        try:
            r, w, e = select.select(self.reading, self.writing, [], timeout)
        except select.error:
            self.__flush_unselectables()
            return
            
        for fd in r + w + e:
            g = self.fd_greenlet[fd]
            # if the greenlet is dead this switches back to g.parent
            # (i.e. here), we use dummy to detect this
            if g.switch(dummy) is dummy:
                # FIXME -- this code-path is untested
                raise AssertionError, 'greenlet is dead: %s' % g

    def __flush_unselectables(self):
        try:
            list = self.reading
            for fd in self.reading:
                select.select([fd], [], [], 0.0)
            list = self.writing
            for fd in self.writing:
                select.select([], [fd], [], 0.0)
        except select.error:
            g = self.fd_greenlet[fd]
            g.switch(sys.exc_info()[1])
        
__all__ = ['Reactor']
