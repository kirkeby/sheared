# vim:nowrap:textwidth=0

import os, stat, errno, mimetypes, sys, traceback

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
        if not self.transport.closed:
            self.transport.close()

class HTTPServerFactory(basic.ProtocolFactory):
    def __init__(self, reactor):
        basic.ProtocolFactory.__init__(self, reactor, HTTPServer)
        
        self.hosts = { }
        self.default_host = None

    def addVirtualHost(self, name, vhost):
        self.hosts[name] = vhost

    def setDefaultHost(self, name):
        self.default_host = name

class HTTPServer(basic.LineProtocol):
    def __init__(self, reactor, transport):
        basic.LineProtocol.__init__(self, reactor, transport, '\n')
        self.where = 'request-line'
        self.collected = ''

    def handle(self, request, reply):
        if request.uri[0]:
            reply.sendErrorPage(http.HTTP_FORBIDDEN)

        if request.headers.has_key('Host'):
            vhost = self.factory.hosts.get(request.headers['Host'], None)
        else:
            vhost = None
        if vhost is None and self.factory.default_host:
            vhost = self.factory.hosts[self.factory.default_host]

        if vhost:
            vhost.handle(request, reply, request.uri[2])
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
                    try:
                        self.handle(self.request, self.reply)
                    except:
                        if not self.reply.decapitated and not self.reply.transport.closed:
                            self.reply.sendErrorPage(http.HTTP_INTERNAL_SERVER_ERROR)
                        raise
                finally:
                    self.reply.done()

    def lastLineReceived(self):
        pass

class VirtualHost:
    def __init__(self):
        self.bindings = []

    def handle(self, request, reply, subpath):
        for root, thing in self.bindings:
            if path == root or path.startswith(root + '/'):
                sub = path[ len(root) - 1 : ]
                thing.handle(request, reply, sub)
        reply.sendErrorPage(http.HTTP_NOT_FOUND)

    def bind(self, root, thing):
        self.bindings.append((root, thing))

class StaticCollection:
    def __init__(self, reactor, root):
        self.reactor = reactor
        self.root = root

    def handle(self, request, reply, subpath):
        path = [self.root]
        for piece in subpath.split('/'):
            if piece == '..':
                if len(path) > 1:
                    path.pop()
            else:
                path.append(piece)

        path = '/'.join(path)
        type, encoding = mimetypes.guess_type(path)
        if not type:
            type = 'application/octet-stream'

        try:
            st = os.stat(path)
            if stat.S_ISDIR(st.st_mode):
                reply.sendErrorPage(http.HTTP_FORBIDDEN)

            elif stat.S_ISREG(st.st_mode):
                file = open(path, 'r')
                file = self.reactor.prepareFile(file)
                reply.headers.setHeader('Last-Modified', http.HTTPDateTime(st.st_mtime))
                reply.headers.setHeader('Content-Length', st.st_size)
                reply.headers.setHeader('Content-Type', type)
                if encoding:
                    reply.headers.setHeader('Content-Encoding', encoding)
                while 1:
                    dat = self.reactor.read(file, 4096)
                    if dat == '':
                        break
                    reply.send(dat)
                reply.done()

            else:
                reply.sendErrorPage(http.HTTP_FORBIDDEN)

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                reply.sendErrorPage(http.HTTP_NOT_FOUND)
            else:
                reply.sendErrorPage(http.HTTP_FORBIDDEN)

__all__ = ['HTTPServerFactory', 'VirtualHost', 'StaticCollection']
