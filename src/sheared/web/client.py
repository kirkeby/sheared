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

from sheared import reactor
from sheared.protocol import http
from sheared.python import io

class ServerError(Exception):
    pass

def parse_netloc(nl):
    if ':' in nl:
        host, port = nl.split(':', 1)
        port = int(port)
    else:
        host = nl
        port = 80

    return host, port

def get(url):
    url = urlparse.urlsplit(url)
    scheme = url[0]
    if not scheme == 'http':
        raise ValueError, 'Only the HTTP scheme is supported'
    host, port = parse_netloc(url[1])
    uri = url[2]
    if url[3]:
        uri = uri + '?' + url[3]
    if url[4]:
        raise ValueError, 'Fragments not supported'
    
    tr = reactor.connect('tcp:%s:%d' % (host, port))
    tr = io.BufferedReader(tr)
    
    try:
        tr.write('GET %s HTTP/1.0\r\n' % uri)
        tr.write('Host: %s:%d\r\n' % (host, port))
        tr.write('\r\n')

        l = tr.readline()
        if l == '':
            raise ServerError, 'Empty reply'
        status = http.HTTPStatusLine(l)

        head = ''
        while 1:
            l = tr.readline()
            if l.strip() == '':
                break
            head = head + l
        headers = http.HTTPHeaders(head)
        
        content = ''
        while 1:
            d = tr.read()
            if d == '':
                break
            content = content + d
        
        return status, headers, content

    finally:
        tr.close()
    
def get_content(*args, **kwargs):
    status, headers, content = get(*args, **kwargs)
    if not status.code == 200:
        raise ServerError, 'StatusCode (%d) not 200' % status.code
    return content
