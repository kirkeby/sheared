# vim:nowrap:textwidth=0

import socket, sys

from sheared.python import coroutine

class Port:
    def __init__(self, reactor, factory, address, family=socket.AF_INET, backlog=5):
        self.factory = factory
        self.address = address
        self.backlog = backlog
        self.family = family
        self.reactor = reactor

    def listen(self):
        self.socket = socket.socket(self.family, socket.SOCK_STREAM)
        self.socket.bind(self.address)
        self.socket.listen(self.backlog)
        self.coroutine = coroutine.Coroutine(self._run)
        self.reactor.addCoroutine(self.coroutine, ())

    def _run(self):
        while 1:
            fd, addr = self.reactor.accept(self.socket)
            transport = self.reactor.createTransport(fd, addr)
            co = self.factory.buildCoroutine(transport)
            self.reactor.addCoroutine(co, ())

class TCPClient:
    def __init__(self, reactor, factory, addr, from_addr=None, family=socket.AF_INET):
        self.factory = factory
        self.from_address = from_addr
        self.to_address = addr
        self.family = family
        self.reactor = reactor
        
    def connect(self):
        self.socket = socket.socket(self.family, socket.SOCK_STREAM)
        if not self.from_address is None:
            self.socket.bind(self.from_address)
        transport = self.reactor.createTransport(self.socket, self.to_address)
        coroutine = self.factory.buildCoroutine(transport)
        try:
            self.reactor.connect(self.socket, self.to_address)
            self.reactor.addCoroutine(self.coroutine, (None,))
        except:
            self.reactor.addCoroutine(self.coroutine, (sys.exc_info(),))
         
