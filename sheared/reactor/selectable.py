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
import stackless, sys, fcntl, socket, os, errno, select, types, traceback, time

from sheared.python import queue
from sheared.reactor import transport

class ReactorFile:
    def __init__(self, fd, reactor):
        self.fd = fd
        self.reactor = reactor
    def fileno(self):
        return self.fd
    def read(self, max=4096):
        return self.reactor.read(self, max)
    def write(self, data):
        self.reactor.write(self, data)
    def seek(self, o, i):
        return os.seek(self.fd, o, i)
    def close(self):
        os.close(self.fd)

class ReactorShutdown(Exception):
    pass

class Reactor:
    def safe_send(self, ch, *what):
        if self.channel_tasklet.has_key(id(ch)):
            apply(ch.send, what)
        else:
            print 'send to dead channel intercepted.'

    def shutdown(self, err=None):
        self.stop = 1
        self.error = err

    def buildselectable(self):
        r, w = [], []
        for fd, (handler, file, channel, argv) in self.waiting.items():
            if handler in [self.handleread, self.handleaccept]:
                r.append(fd)
            elif handler in [self.handlewrite, self.handleconnect]:
                w.append(fd)
            else:
                raise InternalError, ('unknown handler', handler)
        return r, w, r + w

    def flushunselectabels(self, r, w):
        try:
            for fd in r:
                select.select([fd], [], [], 0)
            for fd in w:
                select.select([], [fd], [], 0)
        except select.error, why:
            handler, file, channel, argv = self.waiting[fd]
            del self.waiting[fd]
            self.safe_send(channel, why)
        
    def handleread(self, file, channel, (max)):
        del self.waiting[file.fileno()]
        self.safe_send(channel, os.read(file.fileno(), max))

    def handlewrite(self, file, channel, argv):
        count = os.write(file.fileno(), argv)
        argv = argv[count :]
        if argv:
            self.waiting[file.fileno()] = self.handlewrite, file, channel, argv
        else:
            del self.waiting[file.fileno()]
            self.safe_send(channel, None)
            
    def handleaccept(self, file, channel, argv):
        sock, addr = file.accept()
        del self.waiting[file.fileno()]
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        self.safe_send(channel, (sock, addr))

    def handleconnect(self, file, channel, argv):
        del self.waiting[file.fileno()]
        err = file.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            self.safe_send(channel, socket.error(err, os.strerror(err)))
        else:
            self.safe_send(channel, None)

    def wait(self, file, op, argv):
        channel = self.tasklet_channel[id(stackless.getcurrent())]
        self.waiting[file.fileno()] = op, file, channel, argv
        return channel.receive()
    
    def accept(self, factory, sock):
        try:
            while 1:
                fd, addr = self.wait(sock, self.handleaccept, ())
                t = transport.ReactorTransport(self, fd, addr)
                self.createtasklet(self.startup, (factory, t))

        finally:
            try:
                self.close(sock)
            except:
                traceback.print_exc()

    def startup(self, factory, transport):
        try:
            factory.startup(transport)
        finally:
            transport.close()

    def connectSocket(self, family, type, addr):
        sock = socket.socket(family, type)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        #if not self.from_address is None:
        #    self.socket.bind(self.from_address)
    
        try:
            sock.connect(addr)
        except socket.error, (eno, _):
            if not eno == errno.EINPROGRESS:
                raise

        self.wait(sock, self.handleconnect, ())
        return transport.ReactorTransport(self, sock, addr)

    ### public reactor interface ###
    def __init__(self):
        self.tasklet = stackless.tasklet()

        self.tasklet_channel = {}
        self.channel_tasklet = {}

        self.waiting = {}
        self.sleeping = queue.MinQueue()

        self.started = 0
        self.stopped = 0
        self.stop = 0
        self.error = None
        self.exc_info = None

    def wake_sleepers(self):
        now = self.time()
        while (not self.sleeping.empty()) and (self.sleeping.minkey() <= now):
            channel = self.sleeping.getmin()
            self.safe_send(channel, None)

    def start(self):
        self.started = 1
        self.tasklet.become()

        try:
            while not self.stop:
                self.wake_sleepers()
                while stackless.getruncount() > 1:
                    stackless.schedule()
                    self.wake_sleepers()

                r, w, e = self.buildselectable()
                if self.sleeping.empty():
                    if not (r or w or e):
                        break

                if not self.sleeping.empty():
                    now = self.time()
                    timeout = max(0.0, self.sleeping.minkey() - now)
                else:
                    timeout = None

                try:
                    r, w, e = select.select(r, w, e, timeout)
                except select.error, (eno, emsg):
                    self.flushunselectabels(r, w)

                self.wake_sleepers()

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
                            self.safe_send(channel, sys.exc_info()[1])
                    except:
                        self.safe_send(channel, sys.exc_info()[1])

        except:
            self.exc_info = sys.exc_info()
        self.stopped = 1

    def run(self):
        if not stackless.getmain() is stackless.getcurrent():
            raise RuntimeError, 'reactor not started from main tasklet'
        if not self.started:
            self.start()
        if self.stopped:
            raise RuntimeError, 'reactor already stopped'
        stackless.run()

        if self.exc_info:
            raise self.exc_info[0], self.exc_info[1], self.exc_info[2]
        else:
            return self.error

    def createtasklet(self, func, args=(), kwargs={}):
        t = stackless.tasklet()
        c = stackless.channel()
        self.tasklet_channel[id(t)] = c
        self.channel_tasklet[id(c)] = t

        t.become(c)
        try:
            apply(func, args, kwargs)
        except:
            traceback.print_exc()

        del self.channel_tasklet[id(c)]
        del self.tasklet_channel[id(t)]

    def open(self, path, mode):
        f = open(path, mode)
        fcntl.fcntl(f.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        return f

    def prepareFile(self, file):
        if isinstance(file, types.IntType):
            file = ReactorFile(file, self)
        fcntl.fcntl(file.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        return file

    def read(self, file, max=4096):
        return self.wait(file, self.handleread, (max))

    def write(self, file, data):
        return self.wait(file, self.handlewrite, (data))

    def sendfile(self, i, o):
        while 1:
            d = self.read(i, 4096)
            if d == '':
                break
            self.write(o, d)

    def close(self, file):
        file.close()

    def sleep(self, seconds):
        channel = self.tasklet_channel[id(stackless.getcurrent())]
        self.sleeping.insert(self.time() + seconds, channel)
        return channel.receive()

    def schedule(self):
        if self.started and not self.stopped:
            channel = self.tasklet_channel[id(stackless.getcurrent())]
            self.sleeping.insert(0, channel)
            return channel.receive()
        else:
            stackless.schedule()

    def time(self):
        return time.time()

    def connectTCP(self, addr):
        return self.connectSocket(socket.AF_INET, socket.SOCK_STREAM, addr)
    def connectUNIX(self, addr):
        return self.connectSocket(socket.AF_UNIX, socket.SOCK_STREAM, addr)

    def listenTCP(self, factory, addr, backlog=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        self.createtasklet(self.accept, (factory, sock))

    def listenUNIX(self, factory, addr, backlog=5):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state; does this call make any
        # sense on UNIX sockets?!
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        self.createtasklet(self.accept, (factory, sock))

    def createTransport(self, file, other):
        return transport.ReactorTransport(self, self.prepareFile(file), other)
