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
import stackless
import sys
import fcntl
import socket
import os
import errno
import select
import types
import traceback
import time
import warnings

from sheared.python import queue
from sheared.reactors import base

class Reactor(base.Reactor):
    def __init__(self):
        base.Reactor.__init__(self)
    
        self.tasklet_channel = {}
        self.tasklet_name = {}
        self.channel_tasklet = {}

        self.waiting = {}
        self.sleeping = queue.MinQueue()

    def _run(self):
        self.tasklet_name[id(stackless.getcurrent())] = '<Reactor core>'
        #def cb(p, n):
        #    print str(self.tasklet_name.get(id(n), '[unknown]'))
        #stackless.set_schedule_callback(cb)

        while not self.stopping:
            self._wake_sleepers()
            while stackless.getruncount() > 1:
                stackless.schedule()
                self._wake_sleepers()

            r, w, e = self._buildselectable()
            if self.sleeping.empty():
                if not (r or w or e):
                    break

            if not self.sleeping.empty():
                now = time.time()
                timeout = max(0.0, self.sleeping.minkey() - now)
            else:
                timeout = None

            try:
                r, w, e = select.select(r, w, e, timeout)
            except select.error, (eno, emsg):
                self._flushunselectabels(r, w)
            except ValueError:
                self._flushunselectabels(r, w)

            self._wake_sleepers()

            fds = r + w
            for fd in e:
                if not fd in fds:
                    fds.append(fd)

            for fd in fds:
                if not self.waiting.has_key(fd):
                    continue
                handler, file, channel, argv = self.waiting[fd]
                try:
                    handler(file, channel, argv)
                except socket.error, (eno, estr):
                    if not eno in (errno.EINTR, errno.EAGAIN):
                        self._safe_send(channel, sys.exc_info()[1])
                except SystemExit:
                    raise
                except:
                    self._safe_send(channel, sys.exc_info()[1])

    def _buildselectable(self):
        r, w = [], []
        for fd, (handler, file, channel, argv) in self.waiting.items():
            if handler in [self._handleread, self._handleaccept]:
                r.append(fd)
            elif handler in [self._handlewrite, self._handleconnect]:
                w.append(fd)
            else:
                raise InternalError, ('unknown handler', handler)
        return r, w, r + w

    def _flushunselectabels(self, r, w):
        why = None
        try:
            for fd in r:
                select.select([fd], [], [], 0)
            for fd in w:
                select.select([], [fd], [], 0)
        except select.error, why:
            pass
        except ValueError, why:
            pass

        if why:
            handler, file, channel, argv = self.waiting[fd]
            warnings.warn('fd %d unselectable for %r/%r' % (fd, handler, argv),
                          stacklevel=2)
            del self.waiting[fd]
            self._safe_send(channel, why)

    def _wait(self, file, op, argv):
        assert self.running

        channel = self.tasklet_channel[id(stackless.getcurrent())]
        self.waiting[file.fileno()] = op, file, channel, argv
        return channel.receive()
        
    def _handleread(self, file, channel, (max)):
        del self.waiting[file.fileno()]
        self._safe_send(channel, os.read(file.fileno(), max))

    def _handlewrite(self, file, channel, argv):
        count = os.write(file.fileno(), argv)
        argv = argv[count :]
        if argv:
            self.waiting[file.fileno()] = self._handlewrite, file, channel, argv
        else:
            del self.waiting[file.fileno()]
            self._safe_send(channel, None)

    def _handleconnect(self, file, channel, argv):
        del self.waiting[file.fileno()]
        err = file.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            self._safe_send(channel, socket.error(err, os.strerror(err)))
        else:
            self._safe_send(channel, None)
            
    def _handleaccept(self, file, channel, argv):
        sock, addr = file.accept()
        del self.waiting[file.fileno()]
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        self._safe_send(channel, (sock, addr))
    
    def _accept(self, factory, sock):
        while 1:
            s, a = self._wait(sock, self._handleaccept, ())
            fcntl.fcntl(s.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            t = base.ReactorSocket(s, a, self)
            name = '<server for %r>' % factory
            self.createtasklet(self._startup, (factory, t), name=name)

    def _connectSocket(self, family, type, addr):
        sock = socket.socket(family, type)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        #if not self.from_address is None:
        #    self.socket.bind(self.from_address)
    
        try:
            sock.connect(addr)
        except socket.error, (eno, _):
            if not eno == errno.EINPROGRESS:
                raise

        self._wait(sock, self._handleconnect, ())
        return base.ReactorSocket(sock, addr, self)

    def _wake_sleepers(self):
        now = time.time()
        while (not self.sleeping.empty()) and (self.sleeping.minkey() <= now):
            channel = self.sleeping.getmin()
            self._safe_send(channel, None)

    def _read(self, file, max=4096):
        return self._wait(file, self._handleread, (max))

    def _write(self, file, data):
        return self._wait(file, self._handlewrite, (data))

    def _sendfile(self, i, o):
        while 1:
            d = self._read(i, 4096)
            if d == '':
                break
            self._write(o, d)

    def createtasklet(self, func, args=(), kwargs={}, name=None):
        t = stackless.tasklet()
        c = stackless.channel()
        self.tasklet_channel[id(t)] = c
        self.tasklet_name[id(t)] = name
        self.channel_tasklet[id(c)] = t

        t.setatomic(1)
        t.become(c)
        try:
            try:
                apply(func, args, kwargs)
            except SystemExit:
                raise
            except:
                traceback.print_exc()

        finally:
            del self.channel_tasklet[id(c)]
            del self.tasklet_channel[id(t)]
            del self.tasklet_name[id(t)]

    def sleep(self, seconds):
        if self.running:
            channel = self.tasklet_channel[id(stackless.getcurrent())]
            self.sleeping.insert(time.time() + seconds, channel)
            channel.receive()

        else:
            time.sleep(seconds)
        

    def schedule(self):
        if self.running:
            self.sleep(0)

        else:
            stackless.schedule()
            

    def fdopen(self, file, mode='r', other=None):
        if isinstance(file, types.IntType):
            fd = file
        else:
            fd = file.fileno()
        if self.running:
            fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)
            return base.ReactorFile(file, other, self)
        else:
            return os.fdopen(file, mode)

    def connectTCP(self, addr):
        assert self.running

        return self._connectSocket(socket.AF_INET, socket.SOCK_STREAM, addr)
    def connectUNIX(self, addr):
        assert self.running

        return self._connectSocket(socket.AF_UNIX, socket.SOCK_STREAM, addr)

    def listenTCP(self, factory, addr, backlog=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        name = '<TCP listener for %r>' % factory
        self.createtasklet(self._accept, (factory, sock), name=name)

    def listenUNIX(self, factory, addr, backlog=5):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state; does this call make any
        # sense on UNIX sockets?!
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        os.chmod(addr, 0777)
        sock.listen(backlog)

        name = '<UNIX listener for %r>' % factory
        self.createtasklet(self._accept, (factory, sock), name=name)
