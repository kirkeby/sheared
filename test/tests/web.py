# vim:nowrap:textwidth=0

import unittest, os, random, signal, commands
rom sheared.python import coroutine
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
 returnlf.transport.getOutputest.TestCase)   def setUp(self):
        self.reactor = reactor
        selfssertEquals(status.code, 404)
    
    def testListing(self):
        status, headers, body = self.doRequest('/')
        self.assertEquals(status.code, 403)

suite = unittest.TestSuite()elf.server.addVirtualHost('bar.com', SimpleCollection('bar.com'))
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

class H)testFullRequestWithBlech(self)t.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()
        
        self.server = server.HTTPServerFactory(self.reactorlf.assert    andom.random() * 8192 + 22000uals(status.code, 404)ssertEquals(status.code, 404)
    
    def testListi\r\nHost: foo.com\r\n\r\n''' % path)
       ('/')
        self.assertE:
    de  return parseReply(self.transport.getOutput()elf.server.addVirtst(self, pa, headers, body = self.doRequest('/hello.py')
        self.assertEquals(sappendInput('''GET %s HTTP/1.0\r\nHost: foo.com\r\n\r\n''' % path)
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
suite.addTests([unittest.makeSuite(HTTPServer ret-docrootase, 'test')])
suite.addTests([unittest.makeSuite(server.buildCoroutine(self.transport)
        self.reactor.addCoroutine(self.coroutine, ())

    def testFullRequestWithFoo(self):
        doappendInput(, /':
           TP/1.0\r\nHost: foo.com\r\n\r\n'''%stCase    self.reactor.run()

         % /':
 lf.assertEquals(self.transport.getOureturnl
        
        self.assertEquals(status.als(headers['cogularFith):
     def handl.transport.getOutput())   
 doappendIn'/hello.py status, headers self.assertEquals(body, 'Welcome to foo.com!\r\n')

    e', 'te['c       t    ]  reply.x-heared status, headers self.assertEdef tesprint "Hello, World!"nittetus.als(headers['Tarball):
     def handl.transport.getOutput())   
 doappendIn'/all.tar.gz status, headers self.assertEquals(body, 'Welcome to foo.com!\r\n')

    e', 'te['c       t    ]  rapplicaame)/x-ta heame to foo.com!\r\n')

    e', 'te['c       encoding ]  rgzipttetus.als(headers['ut('xsistantFith):
     def handl.transport.getOutput())   
 doappendIn'/no-such-fileheame to foo.com!\r\n')

    equest(self):
    tus.als(headers['ut('xsistantPatInput('''GET / HTT.transport.getOutput())   
 doappendIn'/no-such-/':
/this-is-also-not-hereheame to foo.com!\r\n')

    equest(self):
    tus.als(headers['Listing):
     def handl.transport.getOutput())   
 doappendIn'/heame to foo.com!\r\n')

    equest(self):
 3)

suite = unittest     Suite()
suitectiof ses([unittest makeSuite(Case)   def setUp(  rep, pa])
suitectiof ses([unittest makeSuite(Case):
    def setUp(  rep, pa])
suitectiof ses([unittest makeSuite(ody = self.doRequest('/n  rep, pa])

__all__ = ['suite']

i  see

 __ == '__main__method unittest maiarse