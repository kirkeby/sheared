# vim:nowrap:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby
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

import time, urlparse, types, re

http_header_classes = {
    'date':              ((1,0), 'general'),
    'pragma':            ((1,0), 'general'),
    
    'authorization':     ((1,0), 'request'),
    'from':              ((1,0), 'request'),
    'if-modified-since': ((1,0), 'request'),
    'referer':           ((1,0), 'request'),
    'user-agent':        ((1,0), 'request'),
    
    'location':          ((1,0), 'response'),
    'server':            ((1,0), 'response'),
    'www-authenticate':  ((1,0), 'response'),

    'allow':             ((1,0), 'entity'),
    'content-encoding':  ((1,0), 'entity'),
    'content-length':    ((1,0), 'entity'),
    'content-type':      ((1,0), 'entity'),
    'expires':           ((1,0), 'entity'),
    'last-modified':     ((1,0), 'entity'),
}
def header_version(name):
    return http_header_classes[name.lower()][0]
def header_class(name):
    return http_header_classes.get(name.lower(), 'unknown')[1]

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
HTTP_NOT_ACCEPTABLE = 406
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
    406: "Not Acceptable",
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

    def __cmp__(self, other):
        return cmp(self.unixtime, other.unixtime)

from sheared.python.rfc822 import RFC822Headers
class HTTPHeaders(RFC822Headers):
    def addHeader(self, name, value):
        key = self.headerKey(name)
        if self.headers.has_key(key):
            self.headers[key].value = self.headers[key].value + ', ' + value
        else:
            self._set(name, value)
    def setHeader(self, name, value):
        self._set(name, value)

    def __getstate__(self):
        return self.items()
    def __setstate__(self, items):
        self.__init__()
        for k, v in items:
            self.addHeader(k, v)

def split_header_list(s):
    l = []
    for e in s.split(','):
        e = e.strip()
        if e:
            l.append(e)
    return l

class HTTPRequestLine:
    def __init__(self, s):
        self.raw = s

        pieces = s.split(' ')
        if len(pieces) == 2 and pieces[0] == 'GET':
            # simple HTTP request-line
            self.method = 'GET'
            self.wire_uri = pieces[1]
            self.uri = urlparse.urlsplit(pieces[1])
            self.version = 0, 9

        elif len(pieces) == 3 and pieces[2].startswith('HTTP/'):
            # full HTTP request-line
            self.method = pieces[0]
            self.wire_uri = pieces[1]
            self.uri = urlparse.urlsplit(pieces[1])
            self.version = tuple(map(int, pieces[2][5:].split('.')))
            if not len(self.version) == 2:
                ValueError('"%s" is not a known form of HTTP request-line' % s)

        else:
            raise ValueError('"%s" is not a known form of HTTP request-line' % s)

class HTTPStatusLine:
    def __init__(self, s):
        all = s.split(' ', 2)
        http, status = all[:2]
        if not http.startswith('HTTP/'):
            raise ValueError, '%r is not a valid HTTP status-line' % s
        if len(all) == 2:
            self.reason = ''
        elif len(all) == 3:
            self.reason = all[2]
        else:
            raise ValueError, '%r is not a valid HTTP status-line' % s

        self.version = tuple(map(int, http[5:].split('.')))
        if not len(self.version) == 2:
            raise ValueError('%r is not a valid HTTP status-line' % s)
        self.code = int(status)

class NotAcceptable(Exception):
    pass
    
def parse_accepts_header(value):
    """parse_accepts_header(header_value) -> widgets

    Parse a HTTP Accept header into a list of acceptable widgets, in
    decreasing order of preference (e.g. [("text/html", 1.0),
    ("text/plain", 0.2)])."""

    widgets = []
    for header in split_header_list(value):
        all = header.split(';')
        if len(all) == 1:
            gizmo, = all
            qval = 1.0
        elif len(all) == 2:
            gizmo, qval = all
            qval = qval.strip()
            if not qval.startswith('q='):
                raise ValueError, 'bad parameter in Accept-header: %s' % qval
            qval = float(qval[2:])
        else:
            raise ValueError, 'bad Accept-header: %s' % value

        gizmo = gizmo.strip()
        if gizmo == '*/*':
            qval = 0.0001
        elif gizmo.endswith('/*'):
            qval = 0.001            
        widget = gizmo, qval
        widgets.append(widget)

    widgets.sort(lambda a, b: cmp(a[1], b[1]))
    return widgets
    
def choose_content_type(accepts, content_types):
    """chooseContentType(request, content_types) -> content_type
    
    Find the preferred content type for a given request, among a list of
    possible content types. Or, if none of the possible content types
    are acceptable raise sheared.error.web.NotAcceptable."""

    if accepts is None:
        accepts = '*/*'

    def is_acceptable(widget, gizmo):
        return (widget == gizmo) or \
               (gizmo.endswith('/*') and widget.startswith(gizmo[:-1])) or \
               (gizmo == '*/*') or \
               (gizmo == '*')

    chosen = None
    acceptable = parse_accepts_header(accepts)
    for content_type in content_types:
        for gizmo, qval in acceptable:
            if is_acceptable(content_type, gizmo):
                if not chosen or qval > chosen[1]:
                    chosen = content_type, qval

    if chosen is None:
        raise NotAcceptable, 'cannot serve any of %s' % accepts

    return chosen[0]

#__all__ = ['HTTPDateTime', 'HTTPHeaders', 'HTTPRequestLine', 'HTTPStatusLine', 'split_header_list']
