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
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket = self.reactor.prepareFile(self.socket)
        self.reactor.bind(self.socket, self.address)
        self.reactor.listen(self.socket, self.backlog)
        self.coroutine = coroutine.Coroutine(self.run)
        self.reactor.addCoroutine(self.coroutine, ())

    def run(self):
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
         
