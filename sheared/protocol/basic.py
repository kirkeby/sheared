# vim:nowrap:textwidth=0

from sheared.python import coroutine

from sheared.internet import error

class ProtocolFactory:
    def __init__(self, protocol):
        self.protocol = protocol

    def buildCoroutine(self, transport):
        p = self.protocol(transport)
        p.factory = self
        return coroutine.Coroutine(p._run, '%s._run' % `p`)

class Protocol:
    def __init__(self, transport):
        self.transport = transport

    def dataReceived(self, data):
        raise NotImplementedError

    def connectionMade(self):
        raise NotImplementedError

    def connectionClosed(self):
        raise NotImplementedError

    def connectionLost(self, reason):
        raise NotImplementedError

    def _run(self):
        while 1:
            data = self.transport.read()
            if data == '':
                break
            self.dataReceived(data)
        self.connectionClosed()

class LineProtocol(Protocol):
    def __init__(self, transport, newline='\n'):
        Protocol.__init__(self, transport)
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

