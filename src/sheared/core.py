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
from errno import EINPROGRESS, EINTR
from heapq import heappush, heappop, _siftdown
from signal import signal, SIG_DFL, SIG_IGN

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
        # mapping file descriptors to greenlets waiting for I/O
        self.reading, self.writing = dictolist(), dictolist()
        # heapq of sleeping processes
        self.sleepers = []
        # mapping blocked on objects to blockees
        self.blockers = dictolist()
        # signal handlers and pending signals
        self.signal_handlers = {}
        self.pending_signals = []
        
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

    # -*- Signal handling -*-
    def signal(self, signo, action):
        if action is SIG_DFL or action is SIG_IGN:
            if signo in self.signal_handlers:
                del self.signal_handlers[signo]
        elif callable(action):
            self.signal_handlers[signo] = action
        else:
            raise ValueError('action neither SIG_DFL, SIG_IGN or callable')
        return signal(signo, self.__handle_signal)

    # -*- Internal greenlet control methods -*-
    def __schedule(self, g, o):
        try:
            if isinstance(o, Exception):
                g.throw(o)
            else:
                g.switch(o)
        except Exception:
            log.error('Uncaught exception in greenlet %s', g, exc_info=True)

    # -*- I/O Convenience methods -*-
    def open(self, *args):
        return ReactorFile(self, open(*args))

    def socket(self, family, type):
        sock = socket(family, type)
        fcntl(sock.fileno(), F_SETFL, os.O_NONBLOCK)
        return ReactorSocket(self, sock)

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

        s = ReactorSocket(self, sock)
        s.here = sock.getsockname()
        s.peer = sock.getpeername()
        return s

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
                t.here = s.getsockname()
                t.peer = s.getpeername()
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
            # FIXME - This leaves a window where we can delay delivery of a
            # signal indefinetly. See http://tinyurl.com/c8h93d for the
            # details, and possible solutions.
            if self.pending_signals:
                self.__handle_signals()
            now = time()
            timeout = self.__wake_sleepers(now)
            if not timeout and not self.reading and not self.writing:
                break
            if not self.state == 'running':
                break
            self.__select(timeout)

    def __cleanup(self):
        err = ReactorExit('Reactor is shutting down')
        for fd in self.reading.keys():
            self.__notify_on_fd(fd, self.reading, err)
        for fd in self.writing.keys():
            self.__notify_on_fd(fd, self.writing, err)

        assert not (self.reading or self.writing)

    # -*- Internal I/O methods called in user greenlets -*-
    def _read(self, fd, max, timeout):
        self.__wait_on_io(fd, self.reading, timeout)
        return os.read(fd, max)
    def _recvfrom(self, sock, max, timeout):
        self.__wait_on_io(sock.fileno(), self.reading, timeout)
        return sock.recvfrom(max)
    def _send(self, sock, bytes, timeout):
        self.__wait_on_io(sock.fileno(), self.writing, timeout)
        return sock.send(bytes)
    def _sendto(self, sock, bytes, flags, addr, timeout):
        self.__wait_on_io(sock.fileno(), self.writing, timeout)
        return sock.sendto(bytes, flags, addr)
    def _write(self, fd, data, timeout):
        self.__wait_on_io(fd, self.writing, timeout)
        return os.write(fd, data)

    def __wait_on_io(self, fd, l, t):
        g = greenlet.getcurrent()
        l.append_to(fd, g)
        if t is not None:
            heappush(self.sleepers, (t, g, EV_TIMEOUT))
        r = g.parent.switch()

        if r is EV_IO_READY:
            return
        elif r is EV_TIMEOUT:
            l.remove_from(fd, g)
            raise TimeoutError()
        else:
            raise AssertionError('I/O-waiting greenlet awoken with %r' % r)

    # -*- Internal I/O methods called in reactor greenlet -*-
    def __wake_sleepers(self, now):
        while self.sleepers and self.sleepers[0][0] <= now:
            t, g, ev = heappop(self.sleepers)
            if t and now - t > 3.0:
                log.info('... greenlet overslept.')
            self.__schedule(g, ev)
        if self.sleepers:
            return self.sleepers[0][0] - now
        else:
            return None

    def __select(self, timeout):
        try:
            r, w, e = select(self.reading.keys(),
                             self.writing.keys(),
                             [],
                             timeout)
            for fd in r:
                self.__notify_on_fd(fd, self.reading)
            for fd in w:
                self.__notify_on_fd(fd, self.writing)
        except SelectError, ex:
            if ex.args[0] <> EINTR:
                log.warn('Error waiting for I/O', exc_info=True)
                self.__flush_unselectables()

    def __notify_on_fd(self, fd, l, ev=EV_IO_READY):
        g = l.pop_from(fd)
        if g.dead:
            # FIXME - Restart notify-on-fd - there might be others waiting.
            log.error('Greenlet %s waiting for IO on fd %d is dead', g, fd)
        else:
            self.__schedule(g, ev)

    def __flush_unselectables(self):
        # Assume there is only one, if there are more, we'll just get called
        # more than once.
        try:
            l = self.reading
            for fd in self.reading:
                select([fd], [], [], 0.0)
            l = self.writing
            for fd in self.writing:
                select([], [fd], [], 0.0)
        except SelectError, err:
            self.__notify_on_fd(fd, l, err)

    # -*- Internal signal handling methods -*-
    def __handle_signal(self, signal, frame):
        handler = self.signal_handlers[signal]
        self.pending_signals.append((signal, handler))
        
    def __handle_signals(self):
        def f(pending):
            for signal, handler in pending:
                try:
                    handler(signal)
                except Exception:
                    log.warn('Exception in signal-handler', exc_info=True)
        self.pending_signals, pending_signals = [], self.pending_signals
        greenlet(f).switch(pending_signals)
        
__all__ = ['Reactor']
