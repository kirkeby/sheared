# vim:nowrap:textwidth=0

import unittest, os, random, signal, commands

from sheared import reactor
from sheared.python import coroutine
from sheared.reactor import transport
from sheared.protocol import http
from sheared.web import server

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
    headers, body = reply.split('\r\n\r\n', 1)
    status, headers = headers.split('\r\n', 1)
    status = http.HTTPStatusLine(status)
    headers = http.HTTPHeaders(headers)

    return status, headers, body

class HTTPServerTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()
        
        self.server = server.HTTPServerFactory(self.reactor, server.HTTPServer)
        self.server.addVirtualHost('foo.com', SimpleCollection('foo.com'))
        self.server.addVirtualHost('bar.com', SimpleCollection('bar.com'))
        self.server.setDefaultHost('bar.com')

        self.transport = transport.StringTransport()
        self.coroutine = self.server.buildCoroutine(self.transport)
        self.reactor.addCoroutine(self.coroutine, ())

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

        self.port = random.random() * 8192 + 22000
            
        self.reactor = reactor
        self.reactor.reset()

        factory = server.HTTPServerFactory(self.reactor, server.HTTPSubServer)
        factory.addVirtualHost('localhost', SimpleCollection('localhost'))
        factory.setDefaultHost('localhost')
        self.reactor.listenUNIX(factory, './test/fifoo')

        factory = server.HTTPServerFactory(reactor, server.HTTPServer)
        factory.addVirtualHost('localhost', server.HTTPSubServerAdapter(reactor, './test/fifoo'))
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

class StaticCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()
        
        self.server = server.HTTPServerFactory(self.reactor, server.HTTPServer)
        self.server.addVirtualHost('foo.com', server.StaticCollection(self.reactor, './test/http-docroot'))

        self.transport = transport.StringTransport()
        self.coroutine = self.server.buildCoroutine(self.transport)
        self.reactor.addCoroutine(self.coroutine, ())

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

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPSubServerTestCase, 'test')])
suite.addTests([unittest.makeSuite(StaticCollectionTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
