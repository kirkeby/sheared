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

import os
import time
import unittest

from sheared.web.collections.filesystem import FilesystemCollection
from sheared.web.collections.entwined import EntwinedCollection
from sheared.web.collections.static import StaticCollection
from sheared.web.virtualhost import VirtualHost

from sheared.protocol import http
from sheared.python import io
from sheared import error

from web import FakeRequest, FakeReply

class FilesystemCollectionTestCase(unittest.TestCase):
    def doRequest(self, coll, uri, request=None):
        reply = FakeReply()
        if not request:
            request = FakeRequest('GET %s HTTP/1.0' % uri)

        try:
            rsrc = coll
            for part in uri.split('/'):
                if not part:
                    continue
                rsrc = rsrc.getChild(request, reply, part)
                rsrc.handle(request, reply, '')

        except error.web.WebServerError, e:
            reply.setStatusCode(e.statusCode)

        return reply
        
    def testRegularFile(self):
        content = io.readfile('./test/http-docroot/hello.py')
        last_mod = os.stat('./test/http-docroot/hello.py')[8]

        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/hello.py')

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'text/x-python')
        self.assertEquals(reply.headers.has_key('content-encoding'), 0)
        self.assertEquals(reply.headers['content-length'], str(len(content)))
        self.assertEquals(http.HTTPDateTime(reply.headers['last-modified']).unixtime,
                          time.gmtime(last_mod))
        self.assertEquals(reply.sent, content)

    def testMultiView(self):
        content = io.readfile('./test/http-docroot/hello.txt')
        last_mod = os.stat('./test/http-docroot/hello.txt')[8]

        coll = FilesystemCollection('./test/http-docroot')
        request = FakeRequest('GET /hello HTTP/1.0')
        request.headers.setHeader('Accept', 'text/plain, text/*')
        reply = self.doRequest(coll, '/hello', request=request)

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'text/plain')
        self.assertEquals(reply.headers.has_key('content-encoding'), 0)
        self.assertEquals(reply.headers['content-length'], str(len(content)))
        self.assertEquals(http.HTTPDateTime(reply.headers['last-modified']).unixtime,
                          time.gmtime(last_mod))
        self.assertEquals(reply.sent, content)

    def testOldConditionalGet(self):
        content = io.readfile('./test/http-docroot/hello.py')
        last_mod = os.stat('./test/http-docroot/hello.py')[8]

        coll = FilesystemCollection('./test/http-docroot')
        request = FakeRequest('GET /hello.py HTTP/1.0')
        request.headers.setHeader('If-Modified-Since',
                                 str(http.HTTPDateTime(0)))
        reply = self.doRequest(coll, '/hello.py', request)

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'text/x-python')
        self.assertEquals(reply.headers.has_key('content-encoding'), 0)
        self.assertEquals(reply.headers['content-length'], str(len(content)))
        self.assertEquals(http.HTTPDateTime(reply.headers['last-modified']).unixtime,
                          time.gmtime(last_mod))
        self.assertEquals(reply.sent, content)
    
    def testCurrentConditionalGet(self):
        content = io.readfile('./test/http-docroot/hello.py')
        last_mod = os.stat('./test/http-docroot/hello.py')[8]

        coll = FilesystemCollection('./test/http-docroot')
        request = FakeRequest('GET /hello.py HTTP/1.0')
        request.headers.setHeader('If-Modified-Since',
                                 str(http.HTTPDateTime(last_mod)))
        reply = self.doRequest(coll, '/hello.py', request)

        self.assertEquals(reply.status, 304)
        self.assertEquals(reply.headers['content-type'], 'text/x-python')
        self.assertEquals(reply.headers.has_key('content-encoding'), 0)
        self.assertEquals(reply.headers['content-length'], str(len(content)))
        self.assertEquals(http.HTTPDateTime(reply.headers['last-modified']).unixtime,
                          time.gmtime(last_mod))
        self.assertEquals(reply.sent, '')
    
    def testFutureConditionalGet(self):
        content = io.readfile('./test/http-docroot/hello.py')
        last_mod = os.stat('./test/http-docroot/hello.py')[8]

        coll = FilesystemCollection('./test/http-docroot')
        request = FakeRequest('GET /hello.py HTTP/1.0')
        request.headers.setHeader('If-Modified-Since',
                                 str(http.HTTPDateTime(int(time.time()))))
        reply = self.doRequest(coll, '/hello.py', request)

        self.assertEquals(reply.status, 304)
        self.assertEquals(reply.headers['content-type'], 'text/x-python')
        self.assertEquals(reply.headers.has_key('content-encoding'), 0)
        self.assertEquals(reply.headers['content-length'], str(len(content)))
        self.assertEquals(http.HTTPDateTime(reply.headers['last-modified']).unixtime,
                          time.gmtime(last_mod))
        self.assertEquals(reply.sent, '')
    
    def testContentEncoding(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/all.tar.gz')

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'application/x-tar')
        self.assertEquals(reply.headers['content-encoding'], 'gzip')
    
    def testNonexsistantFile(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/no-such-file')
        self.assertEquals(reply.status, 404)
    
    def testNonexsistantPath(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/no-such-path/this-is-also-not-here')
        self.assertEquals(reply.status, 404)
        self.assertEquals(reply.status, 404)
    
    def testAllowedListing(self):
        coll = FilesystemCollection('./test/http-docroot', allow_indexing=1)
        reply = self.doRequest(coll, '/sub/')
        self.assertEquals(reply.status, 200)

    def testForbiddenListing(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/sub/')
        self.assertEquals(reply.status, 403)

    def testRedirectOnDirectory(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/sub')
        self.assertEquals(reply.status, 301)
        
class EntwinedCollectionTestCase(unittest.TestCase):
    # FIXME -- really should have the same tests as
    # FilesystemCollectionTestCase.

    def testCreate(self):
        coll = EntwinedCollection(None, './test/http-docroot')
        coll = EntwinedCollection(None, './test/http-docroot',
                allow_indexing=0)
        coll = EntwinedCollection(None, './test/http-docroot',
                allow_indexing=1)

    def testSimple(self):
        coll = EntwinedCollection(None, './test/http-docroot')
        coll.entwiner.template_pages = ['./test/http-docroot/page.html']
        request = FakeRequest('GET /index.html HTTP/1.0')
        reply = FakeReply()

        child = coll.getChild(request, reply, 'index.html')
        child.handle(request, reply, '')
        self.assertEquals(reply.sent, '<body>index.html</body>')

class Gadget:
    def handle(self, request, reply, subpath):
        reply.headers.setHeader('gadget', 'gadget')
        raise NotImplementedError
    def authenticate(self, request, reply):
        pass
class StaticCollectionTestCase(unittest.TestCase):
    def testOneLevel(self):
        gadget = Gadget()
        coll = StaticCollection()
        coll.bind('foo', gadget)
        self.assertEquals(coll.lookup('foo'), gadget)

    def testMultiLevel(self):
        g1 = Gadget()
        g2 = Gadget()
        g3 = Gadget()
        coll = StaticCollection()
        coll.bind('foo', g1)
        coll.bind('bar/foo', g1)
        coll.bind('bar/bar', g2)
        coll.bind('bar/baz', g3)
        self.assertEquals(coll.lookup('foo'), g1)
        self.assertEquals(coll.lookup('bar/foo'), g1)
        self.assertEquals(coll.lookup('bar/bar'), g2)
        self.assertEquals(coll.lookup('bar/baz'), g3)

    def testHandleIndex(self):
        gadget = Gadget()
        request = FakeRequest('GET / HTTP/1.0')
        reply = FakeReply()
    
        coll = StaticCollection()
        coll.bind('index', gadget)
        
        self.assertRaises(NotImplementedError, coll.handle, request, reply, '')
        self.assertEquals(reply.headers['gadget'], 'gadget')

    def testHandleRedirect(self):
        gadget = Gadget()
        request = FakeRequest('GET /foo HTTP/1.0')
        reply = FakeReply()
    
        coll = StaticCollection()
        coll.bind('foo/bar', gadget)
        vh = VirtualHost(coll)
        
        self.assertRaises(error.web.Moved, vh.handle, request, reply)
        self.assertEquals(reply.headers['location'], 'http://foo.com/foo/')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(StaticCollectionTestCase, 'test')])
suite.addTests([unittest.makeSuite(FilesystemCollectionTestCase, 'test')])
suite.addTests([unittest.makeSuite(EntwinedCollectionTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
