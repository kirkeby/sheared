# vim:nowrap:textwidth=0

import os, stat, errno, mimetypes, sys, pickle, re, types

from sheared import error
from sheared import reactor
from sheared.protocol import http
from sheared.python import fdpass
from sheared.python import io

def unscape_querystring(qs):
    qs = qs.replace('+', ' ')
    while 1:
        try:
            before, after = qs.split('%', 1)
        except ValueError:
            break

        if len(after) < 2:
            raise error.web.InputError, 'percent near end of query-string'
        hex, after = after[0:2], after[2:]
        if re.findall('[^0-9a-fA-F]', hex):
            raise error.web.InputError, 'malformed hex-number in query-string'
        qs = before + chr(int(hex, 16)) + after
    return qs

def parse_querystring(qs):
    args = {}
    if not len(qs):
        return args
    for part in qs.split('&'):
        thing = map(unscape_querystring, part.split('=', 1))
        if len(thing) == 1:
            thing = thing[0], ''
        name, value = thing
        if len(name) == 0:
            raise error.web.InputError, 'zero-length name not allowed'
        if re.findall('[^a-zA-Z0-9-_]', name):
            raise error.web.InputError, 'invalid name in query-string'
        if not args.has_key(name):
            args[name] = []
        if len(value):
            args[name].append(UnvalidatedInput(value))
    return args

class UnvalidatedInput:
    def __init__(self, str):
        self.__str = str

    def as_int(self, radix=10):
        try:
            return int(self.__str, radix)
        except ValueError:
            raise error.web.InputError, '%r: invalid integer' % self.__str

    def as_bool(self):
        return bool(self.__str)
    
    def as_str(self, valid):
        if re.findall('[^%s]' % valid, self.__str):
            raise error.web.InputError, '%r: invalid characters in value' % self.__str
        return self.__str

    def as_name(self):
        return self.as_str('a-zA-Z0-9_-')

    def as_word(self):
        return self.as_str('\x21-\x7e')

    def as_text(self):
        return self.as_str('\t\n\r\x20-\x7e')
    
class HTTPQueryString:
    def __init__(self, qs):
        self.dict = parse_querystring(qs)

    def get_one(self, name, *default):
        assert len(default) <= 1
        v = self.get_many(name, list(default))
        if len(v) == 0 and default:
            v = UnvalidatedInput(default[0])
        elif len(v) == 1:
            v = v[0]
        else:
            raise error.web.InputError, '%s: expected scalar-arg, ' \
                                             'got %r' % (name, v)
        return v

    def get_many(self, name, default=None):
        try:
            return self.dict[name]
        except KeyError:
            if default is None:
                raise error.web.InputError, '%s: required argument missing' % name
            else:
                return map(UnvalidatedInput, default)

class HTTPRequest:
    def __init__(self, requestline, querystring, headers):
        self.method = requestline.method
        self.version = requestline.version
        self.scheme = requestline.uri[0]
        self.host = requestline.uri[1]
        self.path = requestline.uri[2]
        self.querystring = querystring
        self.fragment = requestline.uri[4]
        self.args = HTTPQueryString(self.querystring)
        self.headers = headers

    def parent(self):
        # FIXME -- need to return absolute urls
        return self.path[self.path.rfind('/') : ]
    
    def sibling(self, uri):
        return self.parent() + '/' + uri

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
        self.headers.setHeader('Content-Type', 'text/html')

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

    def sendfile(self, file):
        if not self.decapitated:
            self.sendHead()
        self.transport.sendfile(file)

    def sendErrorPage(self, status, text=None):
        self.setStatusCode(status)
        self.headers.setHeader('Content-Type', 'text/plain')
        if not self.decapitated:
            self.sendHead()
        if text:
            self.send(text)
        else:
            self.send("I am terribly sorry, but an error (%d) occured "
                      "while processing your request.\r\n" % status)
        self.done()

    def isdone(self):
        return self.transport.closed

    def done(self):
        if not self.transport.closed:
            self.transport.close()

class HTTPServer:
    def __init__(self):
        self.hosts = {}
        self.default_host = None

    def addVirtualHost(self, name, vhost):
        self.hosts[name] = vhost

    def setDefaultHost(self, name):
        self.default_host = name

    def handle(self, request, reply):
        try:
            if request.scheme or request.host:
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'No HTTP proxying here.')

            if request.headers.has_key('Host'):
                vhost = self.hosts.get(request.headers['Host'], None)
            else:
                vhost = None
            if vhost is None and self.default_host:
                vhost = self.hosts[self.default_host]

            if vhost:
                vhost.handle(request, reply, request.path)
            else:
                reply.sendErrorPage(http.HTTP_NOT_FOUND, 'No such host.')

        except error.web.WebServerError, e:
            if not reply.decapitated and not reply.transport.closed:
                reply.sendErrorPage(e.statusCode, e.args[0])

    def startup(self, transport):
        reader = io.RecordReader(transport, '\r\n')
        requestline = http.HTTPRequestLine(reader.readline().rstrip())
        querystring = requestline.uri[3]

        if requestline.version[0] == 0: # HTTP/0.9
            headers = http.HTTPHeaders()

        elif requestline.version[0] == 1: # HTTP/1.x
            reader = io.RecordReader(reader, '\r\n\r\n')
            # FIXME -- Need to limit how much we are willing to accept
            # here.
            headers = reader.readline()
            headers = http.HTTPHeaders(headers)

            # FIXME -- This needs refactoring badly; this should
            # probably go into Collection, or into a HTTP-method-
            # mixin.
            if headers.has_key('Content-Type'):
                ct = headers.get('Content-Type')
                cl = int(headers.get('Content-Length'))
                if ct == 'application/x-www-form-urlencoded':
                    querystring = reader.read(cl).lstrip()
                else:
                    print 'need handler for Content-Type %r' % ct

        request = HTTPRequest(requestline, querystring, headers)
        reply = HTTPReply(request.version, transport)

        try:
            self.handle(request, reply)

        except:
            if not reply.decapitated and not reply.transport.closed:
                reply.sendErrorPage(http.HTTP_INTERNAL_SERVER_ERROR)
            raise
            
        reply.done()

class VirtualHost:
    def __init__(self, collection):
        self.collection = collection

    def walkPath(self, path):
        roots = [self.collection]
        subpath = ''
        for piece in path.split('/'):
            if piece == '..':
                if len(path) > 1:
                    roots.pop()
            elif piece == '.' or piece == '':
                pass
            else:
                if getattr(roots[-1], 'isWalkable', 0):
                    roots.append(roots[-1].getChild(piece))
                else:
                    subpath = subpath + '/' + piece
        return roots[-1], subpath

    def handle(self, request, reply, path):
        child, subpath = self.walkPath(path)
        #if child is collection:
        #    child = collection.getChild('')
        child.handle(request, reply, subpath)

__all__ = ['HTTPRequest', 'HTTPReply', 'UnvalidatedInput',
           'HTTPQueryString', 'HTTPServer', 'VirtualHost']
