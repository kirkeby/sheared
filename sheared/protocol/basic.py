# vim:nowrap:textwidth=0

import warnings
warnings.warn('The s.p.basic module is deprecated.', DeprecationWarning)

from sheared.python import coroutine

from sheared.internet import error

class ProtocolFactory:
    def __init__(self, reactor, protocol):
        self.reactor = reactor
        self.protocol = protocol

    def buildCoroutine(self, transport):
        p = self.protocol(self.reactor, transport)
        p.factory = self
        return coroutine.Coroutine(p.run, '%s.run' % `p`)

class Protocol:
    def __init__(self, reactor, transport):
        self.reactor = reactor
        self.transport = transport
        self.closed = 0

    def dataReceived(self, data):
        raise NotImplementedError

    def connectionMade(self):
        raise NotImplementedError

    def connectionClosed(self):
        raise NotImplementedError

    def connectionLost(self, reason):
        raise NotImplementedError

    def run(self):
        while not self.transport.closed:
            data = self.transport.read()
            if data == '':
                break
            self.dataReceived(data)
        self.connectionClosed()
        if not self.transport.closed:
            self.transport.close()

class LineProtocol(Protocol):
    def __init__(self, reactor, transport, newline='\n'):
        Protocol.__init__(self, reactor, transport)
        self.buffered = ''
        self.newline = '\n'

    def dataReceived(self, data):
        self.buffered = self.buffered + data

        self.buffered = self.buffered.split(self.newline, 1)
        assert len(self.buffered) in (1, 2)
        while len(self.buffered) > 1:
            self.receivedLine(self.buffered[0] + self.newline)
            self.buffered = self.buffered[1].split(self.newline, 1)

        assert len(self.buffered) == 1
        self.buffered = self.buffered[0]

    def connectionClosed(self):
        self.receivedLine(self.buffered)
        self.lastLineReceived()
        self.buffered = ''

    def connectionLost(self, reason):
        self.lastLineReceived()
        self.buffered = ''

    def receivedLine(self, line):
        raise NotImplementedError

    def lastLineReceived(self):
        raise NotImplementedError

