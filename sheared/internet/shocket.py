# vim:nowrap:textwidth=0

import socket, sys
from sheared.python import coroutine

class Port:
    def __init__(self, reactor, factory, address, family, type, backlog):
        self.factory = factory
        self.address = address
        self.backlog = backlog
        self.family = family
        self.type = type
        self.reactor = reactor

    def listen(self):
        self.socket = socket.socket(self.family, self.type)
        self.socket = self.reactor.prepareFile(self.socket)
        self.reactor.bind(self.socket, self.address)
        self.reactor.listen(self.socket, self.backlog)
        self.coroutine = coroutine.Coroutine(self._run)
        self.reactor.addCoroutine(self.coroutine, ())

    def _run(self):
        while 1:
            fd, addr = self.reactor.accept(self.socket)
            transport = self.reactor.createTransport(fd, addr)
            co = self.factory.buildCoroutine(transport)
            self.reactor.addCoroutine(co, ())

class TCPPort(Port):
    def __init__(self, reactor, factory, address, backlog=5):
        Port.__init__(self, reactor, factory, address, socket.AF_INET, socket.SOCK_STREAM, backlog)

class UNIXPort(Port):
    def __init__(self, reactor, factory, address, backlog=5):
        Port.__init__(self, reactor, factory, address, socket.AF_UNIX, socket.SOCK_STREAM, backlog)

    
class Client:
    def __init__(self, reactor, addr, from_addr, family, type):
        self.from_address = from_addr
        self.to_address = addr
        self.family = family
        self.type = type
        self.reactor = reactor
        
    def connect(self):
        self.socket = socket.socket(self.family, self.type)
        self.socket = self.reactor.prepareFile(self.socket)
        if not self.from_address is None:
            self.socket.bind(self.from_address)
        self.reactor.connect(self.socket, self.to_address)
        transport = self.reactor.createTransport(self.socket, self.to_address)
        return transport

class TCPClient(Client):
    def __init__(self, reactor, address, from_addr):
        Client.__init__(self, reactor, address, from_addr, socket.AF_INET, socket.SOCK_STREAM)

class UNIXClient(Client):
    def __init__(self, reactor, address, from_addr):
        Client.__init__(self, reactor, address, from_addr, socket.AF_UNIX, socket.SOCK_STREAM)
         
