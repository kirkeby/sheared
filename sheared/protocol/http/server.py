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

    def sendErrorPage(self, status):
        self.setStatusCode(status)
        self.headers.setHeader('Content-Type', 'text/plain')
        self.sendHead()
        self.send("""I am terribly sorry, but an error occured while processing your request.""")
        self.done()

    def done(self):
        self.closed = 1
        self.transport.close()

class HTTPServer(basic.ProtocolFactory):
    def __init__(self):
        basic.ProtocolFactory.__init__(self, HTTPSubServer)
        
        self.hosts = { }
        self.default_host = None

    def addVirtualHost(self, name, vhost):
        self.hosts[name] = vhost

    def setDefaultHost(self, name):
        self.default_host = name

class HTTPSubServer(basic.LineProtocol):
    def __init__(self, transport):
        basic.LineProtocol.__init__(self, transport, '\n')
        self.where = 'request-line'
        self.collected = ''

    def handle(self, request, reply):
        if request.headers.has_key('Host'):
            vhost = self.factory.hosts.get(request.headers['Host'], None)
        else:
            vhost = None
        if vhost is None and self.factory.default_host:
            vhost = self.factory.hosts[self.factory.default_host]

        if vhost:
            vhost.handle(request, reply)
        else:
            reply.sendErrorPage(http.HTTP_NOT_FOUND)

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
                self.request.headers = http.HTTPHeaders(self.collected)
                self.reply = HTTPReply(self.request.version, self.transport)
                try:
                    self.handle(self.request, self.reply)
                except:
                    if not self.reply.decapitated:
                        self.reply.sendErrorPage(http.HTTP_INTERNAL_SERVER_ERROR)
                    if not self.reply.closed:
                        self.reply.close()
                    raise

    def lastLineReceived(self):
        pass
 
__all__ = ['HTTPServer']
