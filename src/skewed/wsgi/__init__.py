# vim:syntax=python:textwidth=0
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

class BaseWSGIServer:
    def __call__(self, transport):
        """BaseWSGIServer.__call__(transport)

        Called when a client connects."""

        # read request-line (i.e. "GET /... HTTP/x.y")
        request = transport.readline().rstrip('\r\n')
        try:
            method, uri, protocol = request.split()
        except ValueError:
            transport.write('500 Bad Request\r\n')
            transport.write('Content-Type: text/plain\r\n\r\n'
            transport.write('Bad Request: ' + request + '\r\n')
            transport.close()
            return
    
        # read HTTP headers
        headers = []
        host = ''
        content_type = ''
        content_length = ''
        while 1:
            line = transport.readline().rstrip('\r\n')
            if not line:
                break
            key, val = line.split(':')
            key, val = key.rstrip(), val.lstrip()
            headers.append((key, val))

            key = key.lower()
            if key == 'content-type':
                content_type = val
            elif key == 'content-length':
                content_length = val

        # read HTTP content
        try:
            cl = int(content_length)
        except ValueError:
            cl = None
        if cl is None:
            content = transport.read(MAX_CONTENT_LENGTH)
            if len(content) == MAX_CONTENT_LENGTH and transport.read(1):
                transport.write('500 Bad Request\r\n')
                transport.write('Content-Type: text/plain\r\n\r\n')
                transport.write('Content too long.\r\n')
                transport.close()
                return
        elif cl > MAX_CONTENT_LENGTH:
            transport.write('500 Bad Request\r\n')
            transport.write('Content-Type: text/plain\r\n\r\n')
            transport.write('Content too long.\r\n')
            transport.close()
            return
        else:
            content = transport.read(cl)
            transport.shutdown(0)

        # find WSGI application
        pieces = uri.split('?', 1)
        if len(pieces) == 1:
            path_info, query_string = pieces
        else:
            path_info, query_string = uri, ''
        script_name, path_info = self.find_application(host, path_info)

        env = {
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'http',
            'wsgi.input': StringIO(content),
            'wsgi.errors': StringIO(''), # FIXME
            'wsgi.multithread': 1,
            'wsgi.multiprocess': 0,
            'wsgi.run_once': 0,

            'sheared.version': sheared.__version__,
            
            'REQUEST_METHOD': method.upper(),
            'SCRIPT_NAME': script_name,
            'PATH_INFO': path_info,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': content_type,
            'CONTENT_LENGTH': content_length,
            'SERVER_NAME': transport.here[0],
            'SERVER_PORT': transport.here[1],
            'SERVER_PROTOCOL': protocol,
        }

    def find_application


class WSGIServer(BaseWSGIServer):
    def __init__(self):
        self.
