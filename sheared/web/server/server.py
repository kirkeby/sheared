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

import sys, traceback, types

from sheared import error
from sheared.protocol import http
from sheared.python import io

import oh_nine, one_oh

class HTTPServer:
    def __init__(self):
        self.hosts = {}
        self.default_host = None

        self.oh_nine = oh_nine.Server()
        self.one_oh = one_oh.Server()

    def addVirtualHost(self, name, vhost):
        self.hosts[name] = vhost

    def setDefaultHost(self, name):
        self.default_host = name

    def startup(self, transport):
        try:
            transport = io.BufferedReader(transport)
            requestline = http.HTTPRequestLine(transport.readline().rstrip())

            if requestline.version[0] == 0: # HTTP/0.9
                request, reply = self.oh_nine.parse(transport, requestline)
                self.handle(request, reply)

            elif requestline.version[0] == 1: # HTTP/1.x
                request, reply = self.one_oh.parse(transport, requestline)
                self.handle(request, reply)

            else:
                # FIXME -- is this the Right Thing?
                raise error.web.NotImplementedError, 'HTTP Version not supported'

        except error.web.WebServerError, e:
            self.logInternalError(sys.exc_info())

            if len(e.args) == 1 and isinstance(e.args[0], types.StringType):
                err = e.args[0]
            else:
                err = 'Unknown why?!'

            transport.write('HTTP/1.0 %d %s\r\n' % (e.statusCode, err))
            transport.write('Content-Type: text/plain\r\n\r\n')
            transport.write('Crashing in flames!\r\n')

        except:
            self.logInternalError(sys.exc_info())

    def handle(self, request, reply):
        try:
            if request.requestline.uri[0] or request.requestline.uri[1]:
                raise error.web.ForbiddenError

            if request.headers.has_key('Host'):
                vhost = self.hosts.get(request.headers['Host'], None)
            else:
                vhost = None
            if vhost is None and self.default_host:
                vhost = self.hosts[self.default_host]

            if vhost:
                try:
                    vhost.handle(request, reply)
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

    def logInternalError(self, (tpe, val, tb)):
        traceback.print_exception(tpe, val, tb)

__all__ = ['HTTPServer']
