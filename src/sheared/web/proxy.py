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

import urlparse

from sheared import error
from sheared import reactor
from sheared.python import io

class DumbProxy:
    def handle(self, request, reply):
        try:
            host = request.requestline.uri[1]
            addr = host, 80
            
            uri = list(request.requestline.uri)
            uri[0] = ''
            uri[1] = ''

            transport = reactor.connectTCP(addr)
            
            transport.write('%s %s HTTP/%d.%d\r\n' % (
                                             request.requestline.method,
                                             urlparse.urlunsplit(uri),
                                             request.requestline.version[0],
                                             request.requestline.version[1]))

            for k, v in request.headers.items():
                transport.write('%s: %s\r\n' % (k, v))
            transport.write('\r\n')
            transport.write(request.body)

            reply.transport.sendfile(transport)
            
        except OSError:
            pass

        transport.close()

class DumbProxyPass:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def handle(self, request, reply):
        try:
            version = request.requestline.version[0]
            transport = reactor.connectTCP((self.host, self.port))
            
            transport.write('%s\r\n' % request.requestline.raw)
            if version == 1:
                for k, v in request.headers.items():
                    transport.write('%s: %s\r\n' % (k, v))
                transport.write('\r\n')
                transport.write(request.body)

            reply.transport.sendfile(transport)

        except OSError:
            pass

        transport.close()

class ReversePassProxy:
    def __init__(self, host, port, location):
        self.host = host
        self.port = port
        self.location = location

    def handle(self, request, reply):
        try:
            version = request.requestline.version[0]
            transport = reactor.connectTCP((self.host, self.port))
            transport = io.BufferedReader(transport)
            
            transport.write('%s\r\n' % request.requestline.raw)
            if version == 1:
                for k, v in request.headers.items():
                    transport.write('%s: %s\r\n' % (k, v))
                transport.write('\r\n')
                transport.write(request.body)

            while 1:
                l = transport.readline()
                if l.startswith('Location: '):
                    l = l.replace('http://%s:%d' % (self.host, self.port),
                              self.location)
                reply.transport.write(l)
                if l == '\r\n':
                    break

            reply.transport.sendfile(transport)

        except OSError:
            pass

        transport.close()
