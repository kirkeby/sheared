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
import pickle

from sheared import reactor
from sheared.web import server
from sheared.python import fdpass

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
        pickle.dump((request, subpath), transport)
        transport.close()

class HTTPSubServer(server.HTTPServer):
    def startup(self, transport):
        for i in range(3):
            try:
                sock, addr = fdpass.recv(transport.fileno())
                break
            except:
                pass
        else:
            raise
        addr = pickle.loads(addr)

        data = ''
        read = None
        while not read == '':
            read = transport.read()
            data = data + read
        transport.close()
        request, subpath = pickle.loads(data)

        transport = reactor.openfd(sock, addr)
        reply = server.HTTPReply(request.requestline.version, transport)

        self.handle(request, reply)

__all__ = ['HTTPSubServerAdapter', 'HTTPSubServer']
