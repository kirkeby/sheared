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

def movedHandler(server, exception, request, reply):
    reply.send("This page has moved. You can now find it here:\r\n"
               "  %s\r\n" % reply.headers.get('Location'))

def unauthorizedErrorHandler(server, exception, request, reply):
    reply.send("I need to see some credentials.\r\n")

def forbiddenErrorHandler(server, exception, request, reply):
    reply.send("Forbidden.\r\n")

def notFoundErrorHandler(server, exception, request, reply):
    reply.send("Not found.\r\n")

def internalServerErrorHandler(server, exception, request, reply):
    reply.send('Internal Server Error.\r\n')
    self.logInternalError(exception.args)

def defaultErrorHandler(server, exception, request, reply):
    reply.send("I am terribly sorry, but an error (%d) occured "
               "while processing your request.\r\n" % e.statusCode)
    server.logInternalError(exception)

class HTTPServer:
    def __init__(self):
        self.hosts = {}
        self.default_host = None

        self.oh_nine = oh_nine.Server()
        self.one_oh = one_oh.Server()

        self.errorlog = None

        self.massageRequestCallbacks = []
        self.requestCompletedCallbacks = []
        self.errorHandlers = [
            (Exception,
                defaultErrorHandler),
            (error.web.InternalServerError,
                internalServerErrorHandler),
            (error.web.NotFoundError,
                notFoundErrorHandler),
            (error.web.ForbiddenError,
                forbiddenErrorHandler),
            (error.web.UnauthorizedError,
                unauthorizedErrorHandler),
            (error.web.Moved,
                movedHandler),
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
                request, reply = self.oh_nine.parse(transport, requestline)
                request.other = client
                self.handle(request, reply)

            elif requestline.version[0] == 1: # HTTP/1.x
                request, reply = self.one_oh.parse(transport, requestline)
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
            if not reply.decapitated:
                reply.setStatusCode(e.statusCode)
                reply.headers.setHeader('Content-Type', 'text/plain')
                self.handleWebServerError(e, request, reply)

        for cb in self.requestCompletedCallbacks:
            try:
                cb(request, reply)
            except:
                self.logInternalError(sys.exc_info())
     
    def handleWebServerError(self, exception, request, reply):
        handler = None
        for kls, hnd in self.errorHandlers:
            if isinstance(exception, kls):
                if handler:
                    if issubclass(kls, handler[0]):
                        handler = kls, hnd
                else:
                    handler = kls, hnd

        if not handler:
            raise error.web.InternalServerError

        handler[1](self, exception, request, reply)

    def logInternalError(self, ex):
        if self.errorlog:
            self.errorlog.exception(ex)
        else:
            log.default.exception(ex)

__all__ = ['HTTPServer']
