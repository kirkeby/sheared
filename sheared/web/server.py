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

import os, stat, errno, mimetypes, sys, pickle, re, types, traceback

from sheared import error
from sheared.protocol import http
from sheared.python import fdpass
from sheared.python import io
from sheared.web import querystring

class HTTPRequest:
    def __init__(self, requestline, qs, headers):
        self.method = requestline.method
        self.version = requestline.version
        self.scheme = requestline.uri[0]
        self.host = requestline.uri[1]
        self.path = requestline.uri[2]
        self.querystring = qs
        self.fragment = requestline.uri[4]
        self.args = querystring.HTTPQueryString(self.querystring)
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

        self.handle(request, reply)

    def handle(self, request, reply):
        try:
            if request.scheme or request.host:
                raise error.web.ForbiddenError

            if request.headers.has_key('Host'):
                vhost = self.hosts.get(request.headers['Host'], None)
            else:
                vhost = None
            if vhost is None and self.default_host:
                vhost = self.hosts[self.default_host]

            if vhost:
                try:
                    vhost.handle(request, reply, request.path)
                except error.web.WebServerError:
                    raise
                except:
                    self.logInternalError(sys.exc_info())
                    raise error.web.InternalServerError
            else:
                raise error.web.NotFoundError

        except error.web.WebServerError, e:
            if not reply.decapitated:
                reply.setStatusCode(e.statusCode)
                reply.headers.setHeader('Content-Type', 'text/plain')
                reply.send("I am terribly sorry, but an error (%d) occured "
                           "while processing your request.\r\n" % e.statusCode)
                
        reply.done()

    def logInternalError(self, (tpe, val, tb)):
        traceback.print_exception(tpe, val, tb)

__all__ = ['HTTPRequest', 'HTTPReply', 'HTTPServer']
