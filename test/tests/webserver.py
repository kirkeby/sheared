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

import unittest, os, random

from sheared import reactor
from sheared.web import server, subserver, virtualhost
from sheared.protocol import http
from sheared.python import commands

from tests import transport
from tests.web import SimpleCollection, parseReply

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

    def testFullRequestWithoutHost(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testSimpleRequest(self):
        self.transport.appendInput('''GET /''')
        self.reactor.start()
        self.assertEquals(self.transport.getOutput(), 'Welcome to bar.com!\r\n')

    def testHeadRequest(self):
        self.transport.appendInput('''HEAD / HTTP/1.0\r\n\r\n''')
        self.reactor.start()
    
        status, headers, body = parseReply(self.transport.getOutput())
        self.assertEquals(status.code, 200)
        self.assertEquals(body, '')

    def testOldConditionalRequest(self):
        self.transport.appendInput('GET / HTTP/1.0\r\n'
                                   'If-Modified-Since: Sat, 07 Jul 1979 20:00:00 GMT\r\n'
                                   '\r\n')
        self.reactor.start()
    
        status, headers, body = parseReply(self.transport.getOutput())
        self.assertEquals(headers['Last-Modified'], 'Sat, 07 Jul 1979 21:00:00 GMT')
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testCurrentConditionalRequest(self):
        self.transport.appendInput('GET / HTTP/1.0\r\n'
                                   'If-Modified-Since: Sat, 07 Jul 1979 21:00:00 GMT\r\n'
                                   '\r\n')
        self.reactor.start()
    
        status, headers, body = parseReply(self.transport.getOutput())
        self.assertEquals(headers['Last-Modified'], 'Sat, 07 Jul 1979 21:00:00 GMT')
        self.assertEquals(status.code, 304)
        self.assertEquals(body, '')

    def testNewConditionalRequest(self):
        self.transport.appendInput('GET / HTTP/1.0\r\n'
                                   'If-Modified-Since: Sat, 07 Jul 1979 22:00:00 GMT\r\n'
                                   '\r\n')
        self.reactor.start()
    
        status, headers, body = parseReply(self.transport.getOutput())
        self.assertEquals(headers['Last-Modified'], 'Sat, 07 Jul 1979 21:00:00 GMT')
        self.assertEquals(status.code, 304)
        self.assertEquals(body, '')

    def testMassageReplyHeaders(self):
        def foo(request, reply):
            reply.headers.setHeader('Foo', 'fubar')

        self.server.massageReplyHeadCallbacks.append(foo)
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: foo.com\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to foo.com!\r\n')
        self.assertEquals(headers['Content-Length'], str(len(body)))
        self.assertEquals(headers['Content-Type'], 'text/plain')
        self.assertEquals(headers['Foo'], 'fubar')

    def testErrorMessage(self):
        self.transport.appendInput('''GET /abuse-me HTTP/1.0\r\n\r\n''')
        self.reactor.start()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.code, 403)
        self.assertEquals(body, 'Sod off, cretin!\r\n')
        self.assertEquals(headers['Content-Type'], 'text/plain')
        self.assertEquals(headers['Content-Length'], str(len(body)))
        self.assertEquals(headers.keys(), ['Date', 'Content-Type', 'Content-Length'])

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

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPSubServerTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
