# vim:nowrap:textwidth=0

from sheared.protocol import basic

class EchoServer(basic.LineProtocol):
    def receivedLine(self, line):
        self.transport.write(line)
    def lastLineReceived(self):
        self.transport.close()
