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
import pickle, types

from sheared import error
from sheared import reactor
from sheared.web import server
from sheared.python import fdpass
from sheared.python import io

class HTTPSubServerCollection:
    def __init__(self, path):
        self.path = path

    def getMethodParser(self, _):
        return self.parseAnything
    def parseAnything(self, *args):
        pass

    def handle(self, request, reply, subpath):
        transport = reactor.connectUNIX(self.path)
        fdpass.send(transport.fileno(), reply.transport.fileno(), pickle.dumps(reply.transport.other))
        pickle.dump((request, reply, subpath), transport)
        transport.close()

class HTTPSubServer(server.HTTPServer):
    def startup(self, server_transport):
        for i in range(3):
            try:
                sock, addr = fdpass.recv(server_transport.fileno())
                break
            except:
                pass
        else:
            raise

        addr = pickle.loads(addr)
        client_transport = reactor.openfd(sock, addr)

        data = io.readall(server_transport)
        server_transport.close()

        request, reply, subpath = pickle.loads(data)
        reply.transport = client_transport

        self.handle(request, reply)

__all__ = ['HTTPSubServerAdapter', 'HTTPSubServer']
