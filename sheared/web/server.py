# vim:nowrap:textwidth=0

import os, stat, errno, mimetypes, sys, traceback, pickle

from sheared.protocol import basic
from sheared.protocol import http
from sheared.internet import shocket
from sheared.python import fdpass

def unscape_querystring(qs):
    qs = qs.replace('+', ' ')
    while 1:
        try:
            before, after = qs.split('%', 1)
        except ValueError:
            break
        hex, after = after[0:2], after[2:]
        qs = before + chr(int(hex, 16)) + after
    return qs

def parse_querystring(qs):
    args = {}
    for part in qs.split('&'):
        thing = part.split('=', 1)
        if len(thing) == 2:
            name, value = thing
        else:
            name, value = thing[0], None
        if len(name) == 0:
            continue
        if not args.has_key(name):
            args[name] = []
        args[name].append(value)
    return args

class HTTPQueryString:
    def __init__(self, qs):
        self.dict = parse_querystring(qs)

    def get_int(self, name):
        return int(self.get_scalar(name))

    def get_scalar(self, name):
        v = self.dict[name]
        if len(v) > 1:
            raise ValueError, 'found list-arg where scalar-arg was expected'
        return v[0]

class HTTPRequest:
    def __init__(self, requestline, headers):
        self.method = requestline.method
        self.version = requestline.version
        self.scheme = requestline.uri[0]
        self.host = requestline.uri[1]
        self.path = requestline.uri[2]
        self.querystring = requestline.uri[3]
        self.fragment = requestline.uri[4]
        self.args = HTTPQueryString(self.querystring)
        self.headers = headers

class HTTPReply:
    def __init__(self, version, transport):
        self.transport = transport

        self.status = 200

        if version[0] == 0:
            self.version = 0, 9
        else:
            self.version = 1, 0
        
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

    def sendErrorPage(self, status, text=None):
        self.setStatusCode(status)
        self.headers.setHeader('Content-Type', 'text/plain')
        if not self.decapitated:
            self.sendHead()
        if text:
            self.send(text)
        else:
            self.send("""I am terribly sorry, but an error occured while processing your request.\n""")
        self.done()

    def done(self):
        if not self.transport.closed:
            self.transport.close()

class HTTPServerFactory(basic.ProtocolFactory):
    def __init__(self, reactor, server):
        basic.ProtocolFactory.__init__(self, reactor, server)
        
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
        try:
            try:
                if request.scheme or request.host:
                    reply.sendErrorPage(http.HTTP_FORBIDDEN, 'No HTTP proxying here.')

                if request.headers.has_key('Host'):
                    vhost = self.factory.hosts.get(request.headers['Host'], None)
                else:
                    vhost = None
                if vhost is None and self.factory.default_host:
                    vhost = self.factory.hosts[self.factory.default_host]

                if vhost:
                    vhost.handle(request, reply, request.path)
                else:
                    reply.sendErrorPage(http.HTTP_NOT_FOUND, 'No such host.')
            except:
                if not reply.decapitated and not reply.transport.closed:
                    reply.sendErrorPage(http.HTTP_INTERNAL_SERVER_ERROR, 'Exception.')
                raise
        finally:
            reply.done()

    def receivedLine(self, line):
        self.collected = self.collected + line

        if self.where == 'request-line':
            self.requestline = http.HTTPRequestLine(line.strip())
            self.collected = ''
            self.where = 'headers'
            if self.requestline.version == (0,9):
                self.receivedLine('\r\n')
    
        elif self.where == 'headers':
            if line == '\r\n':
                request = HTTPRequest(self.requestline, http.HTTPHeaders(self.collected))
                reply = HTTPReply(request.version, self.transport)
                self.handle(request, reply)

    def lastLineReceived(self):
        pass

class HTTPSubServerAdapter:
    def __init__(self, reactor, path):
        self.reactor = reactor
        self.path = path

    def handle(self, request, reply, subpath):
        client = shocket.UNIXClient(self.reactor, self.path, None)
        transport = client.connect()
        fdpass.send(transport.fileno(), reply.transport.fileno(), pickle.dumps(reply.transport.other))
        pickle.dump((request, subpath), transport)
        transport.close()

class HTTPSubServer(HTTPServer):
    def run(self):
        for i in range(3):
            try:
                sock, addr = fdpass.recv(self.transport.fileno())
                break
            except:
                pass
        else:
            raise
        addr = pickle.loads(addr)

        data = ''
        read = None
        while not read == '':
            read = self.transport.read()
            data = data + read
        self.transport.close()

        request, subpath = pickle.loads(data)
        self.transport = self.reactor.createTransport(sock, addr)
        reply = HTTPReply(request.version, self.transport)
        self.handle(request, reply)

class VirtualHost:
    def __init__(self):
        self.bindings = []

    def handle(self, request, reply, path):
        for root, thing in self.bindings:
            if path == root or path.startswith(root + '/'):
                sub = path[ len(root) - 1 : ]
                thing.handle(request, reply, sub)
                break
        else:
            reply.sendErrorPage(http.HTTP_NOT_FOUND, '%s: No such resource.' % path)

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
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'Indexing forbidden.')

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
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'You may not view this resource.')

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                reply.sendErrorPage(http.HTTP_NOT_FOUND, 'No such file or directory.')
            else:
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'You may not view this resource.')

__all__ = ['HTTPServerFactory', 'VirtualHost', 'StaticCollection']
