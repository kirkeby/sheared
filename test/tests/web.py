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
from sheared.web import server, subserver, querystring, virtualhost, resource
from sheared.python import commands

from tests import transport

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

class HTTPServerTestCase(unittest.TestCase):
    def setUp(self):
        self.server = server.HTTPServer()
        vh = virtualhost.VirtualHost(SimpleCollection('foo.com'))
        self.server.addVirtualHost('foo.com', vh)
        vh = virtualhost.VirtualHost(SimpleCollection('bar.com'))
        self.server.addVirtualHost('bar.com', vh)
        self.server.setDefaultHost('bar.com')

        self.transport = transport.StringTransport()

        self.reactor = reactor
        self.reactor.createtasklet(self.server.startup, (self.transport,))

    def testFullRequestWithFoo(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: foo.com\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to foo.com!\r\n')

    def testFullRequestWithBar(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: bar.com\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testFullRequestWithBlech(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: blech.com\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testFullRequestWithoutDefault(self):
        self.server.setDefaultHost(None)
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: blech.com\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 404)

    def testSimpleRequest(self):
        self.transport.appendInput('''GET /''')
        self.reactor.start()
        self.assertEquals(self.transport.getOutput(), 'Welcome to bar.com!\r\n')

class HTTPSubServerTestCase(unittest.TestCase):
    def setUp(self):
        try:
            os.unlink('./test/fifoo')
        except:
            pass

        self.port = int(random.random() * 8192 + 22000)
            
        self.reactor = reactor

        factory = subserver.HTTPSubServer()

        vh = virtualhost.VirtualHost(SimpleCollection('localhost'))
        factory.addVirtualHost('localhost', vh)
        factory.setDefaultHost('localhost')
        self.reactor.listenUNIX(factory, './test/fifoo')

        factory = server.HTTPServer()
        vhost = virtualhost.VirtualHost(subserver.HTTPSubServerCollection('./test/fifoo'))
        factory.addVirtualHost('localhost', vhost)
        factory.setDefaultHost('localhost')
        self.reactor.listenTCP(factory, ('127.0.0.1', self.port))

    def testRequest(self):
        def f():
            try:
                argv = ['/bin/sh', '-c',
                        'curl -D - '
                        'http://localhost:%d/ 2>/dev/null' % self.port]
                reply = commands.getoutput(argv[0], argv)
                status, headers, body = parseReply(reply)
            
                self.assertEquals(status.version, (1, 0))
                self.assertEquals(status.code, 200)
                self.assertEquals(body, 'Welcome to localhost!\r\n')

            finally:
                self.reactor.stop()

        self.reactor.createtasklet(f)
        self.reactor.start()

class HTTPQueryStringTestCase(unittest.TestCase):
    def setUp(self):
        qs = 'int=1&hex=babe&str=foo&flag&many=1&many=2'
        self.qs = querystring.HTTPQueryString(qs)

    def testGetOne(self):
        self.assertEquals(self.qs.get_one('int').as_name(), '1')
        self.assertEquals(self.qs.get_one('hex').as_name(), 'babe')
        self.assertEquals(self.qs.get_one('str').as_name(), 'foo')
        self.assertRaises(error.web.InputError, self.qs.get_one, 'flag')
        self.assertRaises(error.web.InputError, self.qs.get_one, 'many')

    def testGetMany(self):
        self.assertEquals(len(self.qs.get_many('int')), 1)
        self.assertEquals(len(self.qs.get_many('hex')), 1)
        self.assertEquals(len(self.qs.get_many('str')), 1)
        self.assertEquals(len(self.qs.get_many('flag')), 0)
        self.assertEquals(len(self.qs.get_many('many')), 2)

class UnvalidatedInputTestCase(unittest.TestCase):
    def setUp(self):
        self.int = querystring.UnvalidatedInput('a', '1')
        self.hex = querystring.UnvalidatedInput('b', 'babe')
        self.str = querystring.UnvalidatedInput('c', 'foo')

    def testInteger(self):
        self.assertEquals(self.int.as_int(), 1)
        self.assertEquals(self.hex.as_int(16), 0xBABE)
        self.assertEquals(self.hex.as_name(), 'babe')
        self.assertRaises(error.web.InputError, self.str.as_int)

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPSubServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPQueryStringTestCase, 'test')])
suite.addTests([unittest.makeSuite(UnvalidatedInputTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
