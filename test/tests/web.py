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

import unittest, os, random, signal, time

from sheared import reactor
from sheared import error
from sheared.protocol import http
from sheared.web import server, subserver, virtualhost, resource
from sheared.web.collections.collection import Collection
from sheared.web.server.request import HTTPRequest
from sheared.python import commands

from tests import transport

class FakeRequest(HTTPRequest):
    def __init__(self, requestline='GET / HTTP/1.0', headers='', body=''):
        requestline = http.HTTPRequestLine(requestline)
        headers = http.HTTPHeaders(headers)
        HTTPRequest.__init__(self, requestline, headers, body)

class FakeReply:
    def __init__(self, head_only=0):
        self.headers = http.HTTPHeaders()
        self.sent = ''
        self.status = 200
        self.head_only = head_only

    def setStatusCode(self, code):
        self.status = code

    def send(self, data):
        self.sent = self.sent + data
    def sendfile(self, file):
        self.send(file.read())
    def done(self):
        self.done = 1

class FakeResource(resource.NormalResource):
    def __init__(self, name='foo'):
        resource.NormalResource.__init__(self)
        self.name = name

    def handle(self, request, reply, subpath):
        content = """Welcome to %s!\r\n""" % self.name
        last_mod = http.HTTPDateTime(300229200)
        
        reply.headers.setHeader('Content-Type', 'text/plain')
        reply.headers.setHeader('Content-Length', len(content))
        reply.headers.setHeader('Last-Modified', last_mod)
        reply.headers.setHeader('ETag', 'abc')
        
        if not request.head_only:
            if request.headers.has_key('If-None-Match'):
                if request.headers['If-None-Match'] == 'abc':
                    raise error.web.NotModified
            
            if request.headers.has_key('If-Modified-Since'):
                when = http.HTTPDateTime(request.headers['If-Modified-Since'])
                if not last_mod > when:
                    raise error.web.NotModified
            
        reply.send(content)
        reply.done()

    def authenticate(self, request, reply):
        pass

class SimpleCollection(Collection):
    def __init__(self, name):
        resource.GettableResource.__init__(self)
        self.name = name
        self.resource = FakeResource(name)

    def getChild(self, request, reply, subpath):
        if subpath == '':
            return self.resource
        elif subpath == 'moved':
            reply.headers.setHeader('Location', '/')
            raise error.web.MovedPermanently
        elif subpath == 'abuse-me':
            reply.headers.setHeader('Foo', 'fubar')
            raise error.web.ForbiddenError, 'Sod off, cretin!'
        elif subpath == 'post':
            return self.resource
        else:
            raise error.web.NotFoundError

def parseReply(reply):
    try:
        headers, body = reply.split('\r\n\r\n', 1)
        status, headers = headers.split('\r\n', 1)
        status = http.HTTPStatusLine(status)
        headers = http.HTTPHeaders(headers)

    except ValueError:
        raise 'Bad reply: %r' % reply

    return status, headers, body
