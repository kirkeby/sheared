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
from sheared.python import commands

from tests import transport

class FakeRequest:
    def __init__(self, uri):
        self.path = uri
        self.headers = http.HTTPHeaders()

class FakeReply:
    def __init__(self):
        self.headers = http.HTTPHeaders()
        self.sent = ''
        self.status = 200

    def send(self, data):
        self.sent = self.sent + data
    def sendfile(self, file):
        self.send(file.read())
    def done(self):
        self.done = 1

class SimpleCollection(resource.GettableResource):
    def __init__(self, name):
        resource.GettableResource.__init__(self)
        self.name = name

    def handle(self, request, reply, subpath):
        if subpath == '':
            reply.headers.setHeader('Content-Type', 'text/plain')
            reply.send("""Welcome to %s!\r\n""" % self.name)
            reply.done()

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
