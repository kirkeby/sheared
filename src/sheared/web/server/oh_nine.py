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

from sheared.protocol import http
import request

class HTTPReply:
    def __init__(self, transport):
        self.transport = transport
        
        self.headers = http.HTTPHeaders()
        self.cookies = {}

        self.decapitated = 0

    def __getstate__(self):
        return self.decapitated
    def __setstate__(self, state):
        self.decapitated = state
        self.transport = None
        self.headers = http.HTTPHeaders()

    def setStatusCode(self, status):
        pass

    def sendHead(self):
        self.decapitated = 1

    def send(self, data):
        self.decapitated = 1
        self.transport.write(data)

    def sendfile(self, file):
        self.decapitated = 1
        self.transport.sendfile(file)

    def done(self):
        self.transport.close()

class Server:
    def parse(self, transport, requestline):
        headers = http.HTTPHeaders()
        body = ''

        req = request.HTTPRequest(requestline, headers, body)
        rep = HTTPReply(transport)

        return req, rep

__all__ = ['Server']
