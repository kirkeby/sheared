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

import sys, traceback, types, errno

from sheared import error
from sheared.protocol import http
from sheared.python import io
from sheared.python import log
from sheared.web import cookie

import oh_nine, one_oh

# The wonderful error messages were lifted from:
# http://archive.salon.com/21st/chal/1998/02/10chal2.html
http_reason = {}
http_reason[http.HTTP_MOVED_PERMANENTLY] = \
    "This site has been moved.\r\n" \
    "We'd tell you where, but then we'd\r\n" \
    "have to delete you.\r\n" \
    "\r\n" \
    "-- Charles Matthews"
http_reason[http.HTTP_MOVED_TEMPORARILY] = \
    http_reason[http.HTTP_MOVED_PERMANENTLY]
http_reason[http.HTTP_UNAUTHORIZED] = \
    "Login incorrect.\r\n" \
    "Only perfect spellers may\r\n" \
    "enter this system.\r\n" \
    "\r\n" \
    "-- Jason Axley"
http_reason[http.HTTP_NOT_FOUND] = \
    "The Web site you seek\r\n" \
    "cannot be located but\r\n" \
    "endless others exist\r\n" \
    "\r\n" \
    "-- Joy Rothke"
# this is a HTTP/1.1 error-code, but the haiku is too good to throw away
#http_reason[http.HTTP_GONE] = \
#    "Having been erased,\r\n" \
#    "The document you're seeking\r\n" \
#    "Must now be retyped.\r\n" \
#    "\r\n" \
#    "-- Judy Birmingham"

def movedHandler(server, exc_info, request, reply):
    send_http_error_page(reply, None)
def notModifiedHandler(server, exc_info, request, reply):
    reply.sendHead()
    reply.done()
def notFoundErrorHandler(server, exc_info, request, reply):
    send_http_error_page(reply, None)

def internalServerErrorHandler(server, exc_info, request, reply):
    send_http_error_page(reply, None)
    server.logInternalError(exc_info[1].args)

def defaultErrorHandler(server, exc_info, request, reply):
    if len(exc_info[1].args) == 1 and isinstance(exc_info[1].args[0], types.StringTypes):
        send_http_error_page(reply, exc_info[1].args[0])
    else:
        send_http_error_page(reply, None)
        log.default.exception(exc_info)

def send_http_error_page(reply, message):
    if not message:
        if http_reason.has_key(reply.status):
            message = http_reason[reply.status]
        else:
            message = "Errors have occurred.\r\n" \
                      "We won't tell you where or why.\r\n" \
                      "Lazy programmers.\r\n" \
                      "\r\n" \
                      "-- Charlie Gibbs\r\n" \
                      "\r\n" \
                      "P.S. The numer of the error is %d." % reply.status

    for name in reply.headers.keys():
        if not http.headerClass(name) in ['general', 'response']:
            reply.headers.delHeader(name)
        if name.lower() == 'location' and \
           not reply.status in [ http.HTTP_MOVED_PERMANENTLY,
                                 http.HTTP_MOVED_TEMPORARILY, ]:
            reply.headers.delHeader(name)
        if name.lower() == 'www-authenticate' and \
           not reply.status in [ http.HTTP_UNAUTHORIZED, ]:
            reply.headers.delHeader(name)

    reply.headers.setHeader('Content-Type', 'text/plain')
    reply.headers.setHeader('Content-Length', str(len(message) + 2))
    reply.send(message + '\r\n')
    reply.done()

class HTTPServer:
    def __init__(self):
        self.hosts = {}
        self.default_host = None

        self.oh_nine = oh_nine.Server()
        self.one_oh = one_oh.Server()

        self.errorlog = None

        self.massageRequestCallbacks = []
        self.massageReplyHeadCallbacks = []
        self.requestCompletedCallbacks = []
        self.errorHandlers = [
            (error.web.WebServerError, defaultErrorHandler),
            (error.web.NotModified, notModifiedHandler),
            (error.web.Moved, movedHandler),
            (error.web.NotFoundError, notFoundErrorHandler),
            (error.web.InternalServerError, internalServerErrorHandler),
        ]

    def addVirtualHost(self, name, vhost):
        self.hosts[name] = vhost

    def setDefaultHost(self, name):
        self.default_host = name

    def setErrorLog(self, l):
        self.errorlog = l

    def startup(self, transport):
        try:
            client = transport.other
            transport = io.BufferedReader(transport)

            rl = transport.readline().rstrip()
            if not rl:
                transport.close()
                return

            try:
                requestline = http.HTTPRequestLine(rl)
            except ValueError:
                raise error.web.BadRequestError, 'could not parse request-line: %r' % rl

            if requestline.version[0] == 0: # HTTP/0.9
                request, reply = self.oh_nine.parse(self, transport, requestline)
                request.other = client
                self.handle(request, reply)

            elif requestline.version[0] == 1: # HTTP/1.x
                request, reply = self.one_oh.parse(self, transport, requestline)
                request.other = client
                self.handle(request, reply)

            else:
                # FIXME -- is this the Right Thing?
                raise error.web.NotImplementedError, 'HTTP Version not supported'

        except error.web.WebServerError, e:
            if len(e.args) == 1 and isinstance(e.args[0], types.StringType):
                err = e.args[0]
            else:
                err = 'Unknown why?!'

            transport.write('HTTP/1.0 %d %s\r\n' % (e.statusCode, err))
            transport.write('Content-Type: text/plain\r\n\r\n')
            transport.write('Crashing in flames!\r\n')

        except OSError, e:
            if e.errno in (errno.ECONNRESET, errno.EPIPE):
                pass
            else:
                raise

        except:
            self.logInternalError(sys.exc_info())

        transport.close()

    def handle(self, request, reply):
        try:
            if not request.headers.has_key('Host'):
                if self.default_host:
                    request.headers.setHeader('Host', self.default_host)
                else:
                    raise error.web.NotFoundError, 'no Host header and no default host'

            try:
                vhost = self.hosts[request.headers['Host']]
                request.hostname = request.headers['Host']
            except KeyError:
                if self.default_host:
                    vhost = self.hosts[self.default_host]
                    request.hostname = self.default_host
                else:
                    raise error.web.NotFoundError, 'unknown host and no default host'

            for cb in self.massageRequestCallbacks:
                cb(request, reply)

            try:
                vhost.handle(request, reply)
            except error.web.WebServerError:
                raise
            except:
                raise error.web.InternalServerError, sys.exc_info()

        except error.web.WebServerError, e:
            reply.setStatusCode(e.statusCode)
            self.handleWebServerError(sys.exc_info(), request, reply)

        for cb in self.requestCompletedCallbacks:
            try:
                cb(request, reply)
            except:
                self.logInternalError(sys.exc_info())
     
    def handleWebServerError(self, exc_info, request, reply):
        handler = None
        for kls, hnd in self.errorHandlers:
            if isinstance(exc_info[1], kls):
                if handler:
                    if issubclass(kls, handler[0]):
                        handler = kls, hnd
                else:
                    handler = kls, hnd

        if not handler:
            raise error.web.InternalServerError

        try:
            handler[1](self, exc_info, request, reply)
        except error.web.NotModified:
            notModifiedHandler(None, None, request, reply)
        except error.web.Moved:
            movedHandler(None, None, request, reply)
        except error.web.WebServerError:
            notFoundErrorHandler(None, None, request, reply)

    def logInternalError(self, exc_info):
        if self.errorlog:
            self.errorlog.exception(exc_info)
        else:
            log.default.exception(exc_info)

__all__ = ['HTTPServer']
