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

import unittest, os, random, signal, commands, time

from sheared import reactor
from sheared import error
from sheared.reactor import transport
from sheared.protocol import http
from sheared.web import server, subserver, collection

class SimpleCollection:
    def __init__(self, name):
        self.name = name

    def handle(self, request, reply, subpath):
        if subpath == '/':
            if not request.method == 'GET':
                reply.sendErrorPage(http.HTTP_METHOD_NOT_SUPPORTED)

            else:
                reply.headers.setHeader('Content-Type', 'text/plain')
                reply.send("""Welcome to %s!\r\n""" % self.name)
                reply.done()

        else:
            reply.sendErrorPage(http.HTTP_NOT_FOUND)

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
        self.reactor = reactor.current.__class__()

        self.server = server.HTTPServer()
        self.server.addVirtualHost('foo.com', SimpleCollection('foo.com'))
        self.server.addVirtualHost('bar.com', SimpleCollection('bar.com'))
        self.server.setDefaultHost('bar.com')

        self.transport = transport.StringTransport()
        self.reactor.createtasklet(self.server.startup, (self.transport,))

    def testFullRequestWithFoo(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: foo.com\r\n\r\n''')
        self.reactor.run()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to foo.com!\r\n')

    def testFullRequestWithBar(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: bar.com\r\n\r\n''')
        self.reactor.run()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testFullRequestWithBlech(self):
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: blech.com\r\n\r\n''')
        self.reactor.run()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 200)
        self.assertEquals(body, 'Welcome to bar.com!\r\n')

    def testFullRequestWithoutDefault(self):
        self.server.setDefaultHost(None)
        self.transport.appendInput('''GET / HTTP/1.0\r\nHost: blech.com\r\n\r\n''')
        self.reactor.run()

        status, headers, body = parseReply(self.transport.getOutput())
        
        self.assertEquals(status.version, (1, 0))
        self.assertEquals(status.code, 404)

    def testSimpleRequest(self):
        self.transport.appendInput('''GET /''')
        self.reactor.run()
        self.assertEquals(self.transport.getOutput(), 'Welcome to bar.com!\r\n')

class HTTPSubServerTestCase(unittest.TestCase):
    def setUp(self):
        try:
            os.unlink('./test/fifoo')
        except:
            pass

        self.port = int(random.random() * 8192 + 22000)
            
        self.reactor = reactor.current

        factory = subserver.HTTPSubServer()
        factory.addVirtualHost('localhost', SimpleCollection('localhost'))
        factory.setDefaultHost('localhost')
        self.reactor.listenUNIX(factory, './test/fifoo')

        factory = server.HTTPServer()
        vhost = server.VirtualHost(subserver.HTTPSubServerCollection('./test/fifoo'))
        factory.addVirtualHost('localhost', vhost)
        factory.setDefaultHost('localhost')
        self.reactor.listenTCP(factory, ('127.0.0.1', self.port))

    def testRequest(self):
        pid = os.fork()
        if pid:
            try:
                reply = commands.getoutput('curl -D - http://localhost:%d/ 2>/dev/null' % self.port)
                status, headers, body = parseReply(reply)
                
                self.assertEquals(status.version, (1, 0))
                self.assertEquals(status.code, 200)
                self.assertEquals(body, 'Welcome to localhost!\r')

            finally:
                os.kill(pid, signal.SIGTERM)
            
        else:
            self.reactor.run()
            sys.exit(0)

class FilesystemCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor.current.__class__()
        
        self.server = server.HTTPServer()
        vhost = server.VirtualHost(collection.FilesystemCollection('./test/http-docroot'))
        self.server.addVirtualHost('foo.com', vhost)

        self.transport = transport.StringTransport()
        self.reactor.createtasklet(self.server.startup, (self.transport,))

    def doRequest(self, path):
        self.transport.appendInput('''GET %s HTTP/1.0\r\nHost: foo.com\r\n\r\n''' % path)
        self.reactor.run()
        return parseReply(self.transport.getOutput())
    
    def testRegularFile(self):
        status, headers, body = self.doRequest('/hello.py')
        self.assertEquals(status.code, 200)
        self.assertEquals(headers['content-type'], 'text/x-python')
        self.assertEquals(body, 'print "Hello, World!"\n')
    
    def testTarball(self):
        status, headers, body = self.doRequest('/all.tar.gz')
        self.assertEquals(status.code, 200)
        self.assertEquals(headers['content-type'], 'application/x-tar')
        self.assertEquals(headers['content-encoding'], 'gzip')
    
    def testNonexsistantFile(self):
        status, headers, body = self.doRequest('/no-such-file')
        self.assertEquals(status.code, 404)
    
    def testNonexsistantPath(self):
        status, headers, body = self.doRequest('/no-such-path/this-is-also-not-here')
        self.assertEquals(status.code, 404)
    
    def testListing(self):
        status, headers, body = self.doRequest('/')
        self.assertEquals(status.code, 403)

class HTTPQueryStringTestCase(unittest.TestCase):
    def setUp(self):
        qs = 'int=1&hex=babe&str=foo&flag&many=1&many=2'
        self.qs = server.HTTPQueryString(qs)

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
        self.int = server.UnvalidatedInput('1')
        self.hex = server.UnvalidatedInput('babe')
        self.str = server.UnvalidatedInput('foo')

    def testInteger(self):
        self.assertEquals(self.int.as_int(), 1)
        self.assertEquals(self.hex.as_int(16), 0xBABE)
        self.assertEquals(self.hex.as_name(), 'babe')
        self.assertRaises(error.web.InputError, self.str.as_int)

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPSubServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(FilesystemCollectionTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPQueryStringTestCase, 'test')])
suite.addTests([unittest.makeSuite(UnvalidatedInputTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
