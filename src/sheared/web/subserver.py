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
import sys, os, pickle, types

from sheared import error
from sheared import reactor
from sheared.web import server
from sheared.python import fdpass
from sheared.python import io

from sheared.python import log

class HTTPSubServerCollection:
    def __init__(self, path):
        self.path = path

    def getMethodParser(self, _):
        return self.parseAnything
    def parseAnything(self, *args):
        pass

    def handle(self, request, reply, subpath):
        try:
            transport = reactor.connectUNIX(self.path)
        except:
            raise error.web.InternalServerError, \
                  'could not connect to sub-server'

        fdpass.send(transport.fileno(), reply.transport.fileno(),
                    pickle.dumps(reply.transport.other))
        pickle.dump((request, reply, subpath), transport)
        transport.close()
        reply.transport.close()

class HTTPSubServer(server.HTTPServer):
    def startup(self, server_transport):
        try:
            server_transport.read(0)
            sock, addr = fdpass.recv(server_transport.fileno())

            addr = pickle.loads(addr)
            client_transport = reactor.fdopen(sock, addr)

            try:
                data = server_transport.read()
                request, reply, subpath = pickle.loads(data)
                server_transport.close()
            
                # FIXME -- There must be a better way to do this
                request.requestline.uri = list(request.requestline.uri)
                request.requestline.uri[0] = ''
                request.requestline.uri[1] = ''
                request.requestline.uri[2] = subpath
                request.requestline.uri = tuple(request.requestline.uri)

                reply.server = self
                reply.transport = client_transport

                self.handle(request, reply)

            finally:
                client_transport.close()

        except:
            self.logInternalError(sys.exc_info())

__all__ = ['HTTPSubServerAdapter', 'HTTPSubServer']
