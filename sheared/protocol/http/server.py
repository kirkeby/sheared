# vim:nowrap:textwidth=0

from sheared.protocol import basic

from sheared.protocol.http import http

class HTTPReply:
    def __init__(self, version, transport):
        self.transport = transport

        self.status = 200
        self.version = version
        
        self.headers = http.HTTPHeaders()
        self.headers.addHeader('Date', str(http.HTTPDateTime()))

        self.decapitated = 0
        self.closed = 0

    def setStatusCode(self, status):
        self.status = status

    def sendHead(self):
        assert not self.decapitated
        self.decapitated = 1

        if self.version == (0,9):
            return

        self.transport.write('HTTP/%d.%d ' % self.version)
        reason = http.http_reason.get(self.status, 'Unknown Status')
        self.transport.write('%d %s\r\n' % (self.status, reason))

        for item in self.headers.items():
            self.transport.write('%s: %s\r\n' % item)

        self.transport.write('\r\n')

    def send(self, data):
        assert not self.closed
        if not self.decapitated:
            self.sendHead()
        self.transport.write(data)

    def sendError(self, status):
        self.setStatusCode(status)
        self.headers.setHeader('Content-Type', 'text/plain')
        self.sendHead()
        self.send("""I am terribly sorry, but an error occured while processing your request.""")
        self.done()

    def done(self):
        self.closed = 1
        self.transport.close()

class HTTPServer(basic.LineProtocol):
    def __init__(self, transport):
        basic.LineProtocol.__init__(self, transport, '\n')
        self.where = 'request-line'
        self.collected = ''

    def handle(self, request, reply):
        reply.sendError(http.HTTP_NOT_FOUND)

    def receivedLine(self, line):
        self.collected = self.collected + line

        if self.where == 'request-line':
            self.request = http.HTTPRequestLine(line.strip())
            self.collected = ''
            self.where = 'headers'
            if self.request.version == (0,9):
                self.receivedLine('\r\n')
    
        elif self.where == 'headers':
            if line == '\r\n':
                self.collected = self.collected[ : -2]
                self.request.headers = http.HTTPHeaders(self.collected)
                self.reply = HTTPReply(self.request.version, self.transport)
                self.handle(self.request, self.reply)
    
                self.collected = ''
                self.where = 'body'

        elif self.where == 'body':
            self.collected = self.collected + line

        else:
            assert 'pigs'.can_fly

    def lastLineReceived(self):
        self.where = ''
        
__all__ = ['HTTPServer']
