# vim:nowrap:textwidth=0

import unittest

from sheared import reactor
from sheared.python import coroutine
from sheared.reactor import transport
from sheared.protocol import basic
from sheared.protocol import http

class HTTPDateTimeTestCase(unittest.TestCase):
    def testAsctime(self):
        """Test HTTPDateTime against ANSI C's asctime date/time format."""
        d = http.HTTPDateTime("Sun Nov 6 08:49:37 1994")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")
        d = http.HTTPDateTime("Sun Nov  6 08:49:37 1994")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")

    def testRFC822(self):
        """Test HTTPDateTime against the RFC 822 date/time format."""
        d = http.HTTPDateTime("Sun, 06 Nov 1994 08:49:37 GMT")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")
        d = http.HTTPDateTime("Sun,   06 Nov 1994 08:49:37 GMT")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")

    def testRFC850(self):
        """Test HTTPDateTime against the RFC 850 date/time format."""
        d = http.HTTPDateTime("Sunday, 06-Nov-94 08:49:37 GMT")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")
        d = http.HTTPDateTime("Sunday, 06-Nov-94   08:49:37 GMT")
        self.assertEquals(str(d), "Sun, 06 Nov 1994 08:49:37 GMT")

class HTTPHeadersTestCase(unittest.TestCase):
    def testEmpty(self):
        """Test HTTPHeaders with no headers."""
        h = http.HTTPHeaders("")
        self.failIf(len(h.items()))

    def testCase(self):
        """Test HTTPHeaders with different cased headers and lookups."""
        h = http.HTTPHeaders("Header: value\r\n" + "some-Other-heAder: Some-Other-value\r\n")

        self.failUnless(h.has_key('header'))
        self.failUnless(h.has_key('some-other-header'))

        self.assertEquals(h.get('header'), 'value')
        self.assertEquals(h.get('header'), 'value')
        self.assertEquals(h['header'], 'value')
        self.assertEquals(h['header'], 'value')

        self.assertEquals(h.get('some-other-header'), 'Some-Other-value')
        self.assertEquals(h.get('SOME-otHer-header'), 'Some-Other-value')
        self.assertEquals(h['some-OtheR-header'], 'Some-Other-value')
        self.assertEquals(h['some-other-heAder'], 'Some-Other-value')

    def testSingleLine(self):
        """Test HTTPHeaders with single-line headers."""
        h = http.HTTPHeaders("Header: value")
        self.assertEquals(h['header'], 'value')
        h = http.HTTPHeaders("Header: value ")
        self.assertEquals(h['header'], 'value ')
        h = http.HTTPHeaders("Header:  value")
        self.assertEquals(h['header'], ' value')

    def testMultiLine(self):
        """Test HTTPHeaders with multi-line headers."""
        h = http.HTTPHeaders("Header: value\r\n\tand this too")
        self.assertEquals(h['header'], 'value\tand this too')

    def testMultiple(self):
        """Test HTTPHeaders with multiple of the same headers."""
        h = http.HTTPHeaders("Header: value\r\nHeader: and this too")
        self.assertEquals(len(http.splitHeaderList(h['header'])), 2)
        self.assertEquals(http.splitHeaderList(h['header'])[0], 'value')
        self.assertEquals(http.splitHeaderList(h['header'])[1], 'and this too')
    def testItems(self):
        """Test HTTPHeaders items method."""
        h = http.HTTPHeaders('One: \r\nTwo: \r\n')
        self.assertEquals(h.items(), [('One', ''), ('Two', '')])

    def testBadHeaders(self):
        """Test HTTPHeaders against some bad HTTP headers."""
        self.assertRaises(ValueError, http.HTTPHeaders, " ")
        self.assertRaises(ValueError, http.HTTPHeaders, "Header:")
        self.assertRaises(ValueError, http.HTTPHeaders, "\r\n Header: bar")

class HTTPRequestLineTestCase(unittest.TestCase):
    def testSimpleRequest(self):
        """Test HTTPRequestLine against a simple HTTP request (version 0.9)."""
        r = http.HTTPRequestLine("GET /")
        self.assertEquals(r.version, (0, 9))
        self.assertEquals(r.method, 'GET')
        self.assertEquals(r.uri, ('', '', '/', '', ''))

    def testFullRequest(self):
        """Test HTTPRequestLine against a full HTTP request."""
        r = http.HTTPRequestLine("GET / HTTP/11.209")
        self.assertEquals(r.version, (11, 209))
        self.assertEquals(r.method, 'GET')
        self.assertEquals(r.uri, ('', '', '/', '', ''))

    def testBadRequestLine(self):
        """Test HTTPRequestLine against some bad HTTP request-lines."""
        self.assertRaises(ValueError, http.HTTPRequestLine, "/")
        self.assertRaises(ValueError, http.HTTPRequestLine, " GET /")
        self.assertRaises(ValueError, http.HTTPRequestLine, "GET / HTTP/1.0 ")
        self.assertRaises(ValueError, http.HTTPRequestLine, "GET\t/ HTTP/1.0")
        self.assertRaises(ValueError, http.HTTPRequestLine, "GET /  HTTP/1.0")

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
    
class HTTPServerFactoryTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()
        
        self.server = http.HTTPServerFactory(self.reactor)
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

class StaticCollectionTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()
        
        self.server = http.HTTPServerFactory(self.reactor)
        self.server.addVirtualHost('foo.com', http.StaticCollection(self.reactor, './tests/http-docroot'))

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
suite.addTests([unittest.makeSuite(HTTPDateTimeTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPHeadersTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPRequestLineTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPServerFactoryTestCase, 'test')])
suite.addTests([unittest.makeSuite(StaticCollectionTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
