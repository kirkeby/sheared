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

from sheared import error
from sheared.protocol import http
from sheared.web import cookie

class HTTPReply:
    def __init__(self, transport, version):
        self.transport = transport

        self.status = 200
        self.version = version
        
        self.headers = http.HTTPHeaders()
        self.headers.addHeader('Date', str(http.HTTPDateTime()))
        self.headers.setHeader('Content-Type', 'text/html')

        self.cookies = []

        self.decapitated = 0

    def __getstate__(self):
        return self.status, self.version, self.headers, self.decapitated
    def __setstate__(self, state):
        self.status, self.version, self.headers, self.decapitated = state
        self.transport = None

    def setStatusCode(self, status):
        self.status = status

    def sendHead(self):
        assert not self.decapitated
        self.decapitated = 1

        self.transport.write('HTTP/%d.%d ' % self.version)
        reason = http.http_reason.get(self.status, 'Unknown Status')
        self.transport.write('%d %s\r\n' % (self.status, reason))

        for c in self.cookies:
            self.headers.addHeader('Set-Cookie', cookie.format(c))

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

    def done(self):
        self.transport.close()

class Server:
    def readBeast(self, transport):
        # read headers
        lines = ''
        while 1:
            line = transport.readline()
            if line == '\r\n':
                break
            lines = lines + line
            
            # FIXME
            if len(lines) > 1024:
                raise error.web.BadRequestError, 'too long head'

        headers = http.HTTPHeaders(lines)

        # read body
        if headers.has_key('Content-Length'):
            cl = int(headers.get('Content-Length'))
            # FIXME
            if cl > 1024 * 100:
                raise error.web.BadRequestError, 'too long body'
            body = transport.read(cl)
        else:
            body = ''

        return headers, body

__all__ = ['Server', 'Reply']
