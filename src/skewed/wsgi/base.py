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

import sheared
from cStringIO import StringIO

import logging
log = logging.getLogger('skewed.wsgi.BaseWSGIServer')

MAX_HEAD_LENGTH = 1024
MAX_CONTENT_LENGTH = 1024

class Response:
    def __init__(self, transport):
        self.transport = transport
        self.decapitated = 0
        self.started = 0
        self.status = None
        self.headers = None

    def start_response(self, status, headers, exc_info=None):
        if exc_info:
            try:
                if self.decapitated:
                    # Re-raise original exception if headers sent
                    raise exc_info[0], exc_info[1], exc_info[2]
            finally:
                exc_info = None # avoid dangling circular ref
        elif self.started:
            raise AssertionError("start_response already called")

        self.started = 1
        self.status = status
        self.headers = headers

        return self.write

    def write(self, data):
        if not self.started:
            raise AssertionError('start_response not called')

        if not self.decapitated:
            self.decapitated = 1
            self.transport.write('HTTP/1.0 ' + self.status + '\r\n')
            for key, val in self.headers:
                self.transport.write(key + ': ' + val + '\r\n')
            self.transport.write('\r\n')

        self.transport.write(data)

    def send_error_page(self, status, why):
        if self.decapitated:
            return

        self.transport.write('HTTP/1.0 ' + status + '\r\n')
        self.transport.write('Content-Type: text/plain\r\n')
        self.transport.write('\r\n')
        self.transport.write(why)

class BadRequestError(Exception):
    pass

class BaseWSGIServer:
    def __init__(self):
        pass

    def __call__(self, transport):
        """BaseWSGIServer.__call__(transport)

        Called when a client connects."""

        try:
            response = Response(transport)
            try:
                self.__handle_request(transport, response)

            except BadRequestError, why:
                log.error('Bad Request: ' + why.rstrip('\r\n'))
                response.send_error_page('500 Bad Request', why)

            except:
                log.exception('Internal Server Error')
                response.send_error_page('500 Internal Server Error',
                                         'Internal Error\r\n')

        finally:
            transport.close()

    def __handle_request(self, transport, response):
        # read request-line (i.e. "GET /... HTTP/x.y")
        request = transport.readline().rstrip('\r\n')
        try:
            method, uri, protocol = request.split()
        except ValueError:
            raise BadRequestError, 'Bad Request: ' + request + '\r\n'
    
        # read HTTP headers
        hl = 0
        headers = []
        host = ''
        content_type = ''
        content_length = ''
        while 1:
            line = transport.readline().rstrip('\r\n')
            hl = hl + len(line) + 2
            if hl > MAX_HEAD_LENGTH:
                raise BadRequestError, 'Headers too long.\r\n'
            if not line:
                break
            key, val = line.split(':', 1)
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
            content = ''
            transport.shutdown(0)
        elif cl > MAX_CONTENT_LENGTH:
            raise BadRequestError, 'Content too long.\r\n'
        else:
            content = transport.read(cl)
            transport.shutdown(0)

        # find WSGI application
        pieces = uri.split('?', 1)
        if len(pieces) == 1:
            path_info, query_string = uri, ''
        else:
            path_info, query_string = pieces
        app, script_name, path_info = self.find_application(host, path_info)

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
            'SERVER_PORT': str(transport.here[1]),
            'SERVER_PROTOCOL': protocol,
        }
        for key, val in headers:
            if key.lower() in ('Content-Type', 'Content-Length'):
                continue
            env['HTTP_' + key.upper().replace('-', '_')] = val

        result = app(env, response.start_response)
        try:
            for data in result:
                if data: # don't send headers until body appears
                    response.write(data)
            if not response.decapitated:
                response.write('')
        finally:
            if hasattr(result, 'close'):
                result.close()

    def find_application(self, host, path):
        raise NotImplementedError

