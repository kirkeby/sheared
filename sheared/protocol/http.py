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

from __future__ import generators

import time, urlparse, types, base64

def headerKey(n):
    return n.lower()

http_header_classes = {
    headerKey('Date'):              ((1,0), 'general'),
    headerKey('Pragma'):            ((1,0), 'general'),
    
    headerKey('Authorization'):     ((1,0), 'request'),
    headerKey('From'):              ((1,0), 'request'),
    headerKey('If-Modified-Since'): ((1,0), 'request'),
    headerKey('Referer'):           ((1,0), 'request'),
    headerKey('User-Agent'):        ((1,0), 'request'),
    
    headerKey('Location'):          ((1,0), 'response'),
    headerKey('Server'):            ((1,0), 'response'),
    headerKey('WWW-Authenticate'):  ((1,0), 'response'),

    headerKey('Allow'):             ((1,0), 'entity'),
    headerKey('Content-Encoding'):  ((1,0), 'entity'),
    headerKey('Content-Length'):    ((1,0), 'entity'),
    headerKey('Content-Type'):      ((1,0), 'entity'),
    headerKey('Expires'):           ((1,0), 'entity'),
    headerKey('Last-Modified'):     ((1,0), 'entity'),
}
def headerVersion(name):
    return http_header_classes[headerKey(name)][0]
def headerClass(name):
    return http_header_classes[headerKey(name)][1]

HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_NO_CONTENT = 204
HTTP_MOVED_PERMANENTLY = 301
HTTP_MOVED_TEMPORARILY = 302
HTTP_NOT_MODIFIED = 304
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_NOT_IMPLEMENTED = 501
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503

http_reason = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Moved Temporarily",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

#
# FIXME -- The following (from RFC 1945 appendix B) describes behaivour which
# cannot be said to apply to this implementation, this should probably be made
# so.
#
# B.  Tolerant Applications
# 
#    Although this document specifies the requirements for the generation
#    of HTTP/1.0 messages, not all applications will be correct in their
#    implementation. We therefore recommend that operational applications
#    be tolerant of deviations whenever those deviations can be
#    interpreted unambiguously.
# 
#    Clients should be tolerant in parsing the Status-Line and servers
#    tolerant when parsing the Request-Line. In particular, they should
#    accept any amount of SP or HT characters between fields, even though
#    only a single SP is required.
# 
#    The line terminator for HTTP-header fields is the sequence CRLF.
#    However, we recommend that applications, when parsing such headers,
#    recognize a single LF as a line terminator and ignore the leading CR.
#

class HTTPDateTime:
    def __init__(self, s=None):
        if isinstance(s, types.IntType):
            self.unixtime = time.gmtime(s)
        elif s:
            self.unixtime = self.parseString(s)
        else:
            self.unixtime = time.gmtime(time.time())

    def parseString(self, s):
        # RFC 822 format (Sun, 06 Nov 1994 08:49:37 GMT)
        try:
            return time.strptime(s, "%a, %d %b %Y %H:%M:%S GMT")
        except ValueError:
            pass
        # RFC 850 format (Sunday, 06-Nov-94 08:49:37 GMT)
        try:
            return time.strptime(s, "%A, %d-%b-%y %H:%M:%S GMT")
        except ValueError:
            pass
        # ANSI C's asctime format (Sun Nov  6 08:49:37 1994)
        try:
            return time.strptime(s, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            pass
        raise ValueError('string matches no known date/time format')

    def __str__(self):
        return time.strftime("%a, %d %b %Y %H:%M:%S GMT", self.unixtime)

def parseHeaderLines(s):
    lines = []
    physical = s.split('\r\n')
    for line in physical:
        if line == '':
            continue
        if line[0] in '\t ':
            if not lines:
                raise ValueError('first line cannot be a continued line')
            lines[-1] = lines[-1] + line
        else:
            lines.append(line)

    for line in lines:
        yield parseHeaderLine(line)

def parseHeaderLine(s):
    try:
        name, value = s.split(': ')
        if not name:
            raise ValueError
    except ValueError:
        raise ValueError('"%s" is not a proper HTTP header' % s)
    return name, value

def splitHeaderList(s):
    l = []
    for e in s.split(','):
        e = e.strip()
        if e:
            l.append(e)
    return l

class HTTPHeaders:
    def __init__(self, s=None):
        self.order = []
        self.headers = {}
        if not s is None:
            for name, value in parseHeaderLines(s):
                self.addHeader(name, value)

    def addHeader(self, name, value):
        key = headerKey(name)
        if not self.headers.has_key(key):
            self.order.append(name)
            self.headers[key] = (name, value)
        else:
            self.headers[key] = (self.headers[key][0], self.headers[key][1] + ', ' + value)
    
    def setHeader(self, name, value):
        key = headerKey(name)
        if not self.headers.has_key(key):
            self.order.append(name)
        self.headers[key] = (name, value)
        
    def get(self, name):
        return self.headers[headerKey(name)][1]
    def __getitem__(self, name):
        return self.get(name)
    def has_key(self, name):
        return self.headers.has_key(headerKey(name))
    def item(self, name):
        return name, self.get(name)
    def items(self):
        return map(self.item, self.order)

def getAuthentication(request):
    login, password = None, None

    if request.headers.has_key('authorization'):
        auth = request.headers['authorization']
        try:
            type, auth = auth.split(' ', 2)

            if type == 'Basic':
                auth = base64.decodestring(auth)
                login, password = auth.split(':', 2)
            else:
                return None, None

        except:
            pass

    return login, password

class HTTPRequestLine:
    def __init__(self, s):
        pieces = s.split(' ')
        if len(pieces) == 2 and pieces[0] == 'GET':
            # simple HTTP request-line
            self.method = 'GET'
            self.uri = urlparse.urlsplit(pieces[1])
            self.version = 0, 9

        elif len(pieces) == 3 and pieces[2].startswith('HTTP/'):
            # full HTTP request-line
            self.method = pieces[0]
            self.uri = urlparse.urlsplit(pieces[1])
            self.version = tuple(map(int, pieces[2][5:].split('.')))
            if not len(self.version) == 2:
                ValueError('"%s" is not a known form of HTTP request-line' % s)

        else:
            raise ValueError('"%s" is not a known form of HTTP request-line' % s)

class HTTPStatusLine:
    def __init__(self, s):
        http, status, self.reason = s.split(' ', 2)
        if not http.startswith('HTTP/'):
            raise ValueError('"%s" is not a valie HTTP status-line' % s)

        self.version = tuple(map(int, http[5:].split('.')))
        if not len(self.version) == 2:
            raise ValueError('"%s" is not a valie HTTP status-line' % s)
        self.code = int(status)

#__all__ = ['HTTPDateTime', 'HTTPHeaders', 'HTTPRequestLine', 'HTTPStatusLine', 'splitHeaderList']
