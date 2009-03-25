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
from heapq import heappush, heappop, _siftdown

from sheared.prelude import parse_address_uri, ReactorFile, ReactorSocket
from sheared.prelude import dictolist
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
        self.blockers = dictolist()
        
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
    def block_on(self, o, timeout=None):
        g = greenlet.getcurrent()
        if timeout is None:
            it = (sys.maxint, g, EV_TIMEOUT)
        else:
            it = (time() + timeout, g, EV_TIMEOUT)
        heappush(self.sleepers, it)
        self.blockers.append_to(o, it)

        r = g.parent.switch()
        if r is EV_TIMEOUT:
            self.blockers.remove_from(o, it)
            raise TimeoutError()
        return r

    def notify_on(self, o, what):
        it = self.blockers.pop_from(o)
        i = self.sleepers.index(it)
        self.sleepers[i] = (0, it[1], what)
        _siftdown(self.sleepers, 0, i)

    def sleep(self, seconds):
        g = greenlet.getcurrent()
        heappush(self.sleepers, (time() + seconds, g, EV_TIMEOUT))
        r = g.parent.switch()
        if not r is EV_TIMEOUT:
            raise AssertionError('sleeping greenlet awoken with %r' % r)

    def spawn(self, function, args=(), kwargs={}):
        g = greenlet(function)
        heappush(self.sleepers, (0.0, g.parent, EV_TIMEOUT))
        g.parent = g.parent.parent
        g.switch(*args, **kwargs)

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
            heappush(self.sleepers, (t, g, EV_TIMEOUT))
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
            t, g, ev = heappop(self.sleepers)
            if t and now - t > 3.0:
                log.info('... greenlet overslept.')
            g.switch(ev)
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
