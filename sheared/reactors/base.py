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
import os
import warnings

from sheared import error

def parse_address_uri(where):
    domain, address = where.split(':', 1)

    if domain == 'tcp':
        ip, port = address.split(':')
        if ip == '*':
            ip = ''
        port = int(port)
        address = ip, port

    elif domain == 'unix':
        pass

    else:
        raise 'Unknown domain: %s' % domain

    return domain, address

class NoReactorFile:
    def __init__(self, fd, other, reactor):
        self.fd = fd
        self.other = other
        self.reactor = reactor
        self.closed = 0
    def __repr__(self):
        return '<NoReactorFile %s>' % self.other
    def fileno(self):
        return self.fd
    def read(self, max=4096):
        if self.reactor.running:
            raise error.reactor.ReactorRunningError, 'Reactor is running'
        return os.read(self.fd, max)
    def write(self, data):
        if self.reactor.running:
            raise error.reactor.ReactorRunningError, 'Reactor is running'
        os.write(self.fd, data)
    def seek(self, o, i):
        return os.lseek(self.fd, o, i)
    def close(self):
        if not self.closed:
            os.close(self.fd)
        self.closed = 1

class ReactorFile:
    def __init__(self, fd, other, reactor):
        self.fd = fd
        self.other = other
        self.reactor = reactor
        self.closed = 0
    def __del__(self):
        self.close()
    def __repr__(self):
        return '<ReactorFile %s>' % self.other

    def fileno(self):
        return self.fd
    def read(self, max=4096):
        return self.reactor._read(self, max)
    def write(self, data):
        self.reactor._write(self, data)
    def sendfile(self, file):
        self.reactor._sendfile(file, self)
    def seek(self, o, i):
        return os.lseek(self.fd, o, i)
    def close(self):
        if not self.closed:
            os.close(self.fd)
        self.closed = 1

class ReactorSocket(ReactorFile):
    def __init__(self, sock, other, reactor):
        ReactorFile.__init__(self, sock.fileno(), other, reactor)
        self.socket = sock
    def __repr__(self):
        return '<ReactorSocket %s>' % self.socket
    def close(self):
        if not self.closed:
            self.socket.close()
        self.closed = 1

class Reactor:
    def __init__(self):
        self.running = 0
        self.stopping = 0
        self.result = None

    def _safe_send(self, ch, *what):
        assert self.running

        if self.channel_tasklet.has_key(id(ch)):
            apply(ch.send, what)
        else:
            warnings.warn('send to dead channel intercepted: %r' % what,
                          stacklevel=2)
    def _startup(self, factory, transport):
        factory.startup(transport)

    def __run(self):
        try:
            self.running = 1
            t = stackless.tasklet()
            t.setatomic(1)
            t.capture()
            self._run()
        finally:
            self.running = 0
            self.stopping = 0
        
    def start(self):
        if not stackless.getmain() is stackless.getcurrent():
            raise RuntimeError, 'reactor not started from main tasklet'
        if self.running:
            raise RuntimeError, 'reactor already running'

        self.__run()
        while self.running:
            stackless.run()

        return self.result

    def stop(self, r=None):
        self.stopping = 1
        self.result = r

    def createtasklet(self, func, args=(), kwargs={}):
        raise NotImplementedError

    def sleep(self, seconds):
        raise NotImplementedError

    def schedule(self):
        raise NotImplementedError

    def open(self, path, flags='r', mode=0600):
        if flags == 'r':
            flags = os.O_CREAT | os.O_RDONLY
        elif flags == 'w':
            flags = os.O_CREAT | os.O_WRONLY
        else:
            raise ValueError, 'unknown flags %r' % flags
        file = self.fdopen(os.open(path, flags, mode), other=path)
        return file

    def fdopen(self, file, mode='r', other=None):
        raise NotImplementedError

    def connect(self, where):
        domain, address = parse_address_uri(where)
        if domain == 'tcp':
            return self.connectTCP(factory, address)
        elif domain == 'unix':
            return self.connectUNIX(factory, address)

    def connectTCP(self, addr):
        raise NotImplementedError

    def connectUNIX(self, addr):
        raise NotImplementedError

    def listen(self, factory, where):
        domain, address = parse_address_uri(where)
        if domain == 'tcp':
            return self.listenTCP(factory, address)
        elif domain == 'unix':
            return self.listenUNIX(factory, address)
    
    def listenTCP(self, factory, addr, backlog=5):
        raise NotImplementedError

    def listenUNIX(self, factory, addr, backlog=5):
        raise NotImplementedError

