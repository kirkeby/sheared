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

import unittest

from sheared.web.collections.filesystem import FilesystemCollection
from sheared.web.collections.static import StaticCollection

from sheared.protocol import http
from sheared import error

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

class FilesystemCollectionTestCase(unittest.TestCase):
    def doRequest(self, coll, uri):
        reply = FakeReply()
        request = FakeRequest(uri)

        rsrc = coll
        for part in uri.split('/'):
            if not part:
                continue
            rsrc = rsrc.getChild(request, reply, part)
        rsrc.handle(request, reply, '')

        return reply
        
    def testRegularFile(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/hello.py')

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'text/x-python')
        self.assertEquals(reply.sent, 'print "Hello, World!"\n')
    
    def testTarball(self):
        coll = FilesystemCollection('./test/http-docroot')
        reply = self.doRequest(coll, '/all.tar.gz')

        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers['content-type'], 'application/x-tar')
        self.assertEquals(reply.headers['content-encoding'], 'gzip')
    
    def testNonexsistantFile(self):
        coll = FilesystemCollection('./test/http-docroot')
        self.assertRaises(error.web.NotFoundError,
                          self.doRequest, coll, '/no-such-file')
    
    def testNonexsistantPath(self):
        coll = FilesystemCollection('./test/http-docroot')
        self.assertRaises(error.web.NotFoundError,
                          self.doRequest, coll, '/no-such-path/this-is-also-not-here')
    
    def testAllowedListing(self):
        coll = FilesystemCollection('./test/http-docroot', allow_indexing=1)
        reply = self.doRequest(coll, '/sub/')

        self.assertEquals(reply.status, 200)

    def testForbiddenListing(self):
        coll = FilesystemCollection('./test/http-docroot')
        self.assertRaises(error.web.ForbiddenError,
                          self.doRequest, coll, '/sub/')

    def testRedirectOnDirectory(self):
        coll = FilesystemCollection('./test/http-docroot')
        self.assertRaises(error.web.MovedPermanently,
                          self.doRequest, coll, '/sub')
        

class Gadget:
    def handle(self, request, reply, subpath):
        reply.headers.setHeader('gadget', 'gadget')
        raise NotImplementedError
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
        class FakeRequest:
            path = '/'
        request = FakeRequest()
        class FakeReply:
            headers = http.HTTPHeaders()
        reply = FakeReply()
    
        coll = StaticCollection()
        coll.bind('index', gadget)
        
        self.assertRaises(NotImplementedError, coll.handle, request, reply, '')
        self.assertEquals(reply.headers['gadget'], 'gadget')

    def testHandleRedirect(self):
        gadget = Gadget()
        class FakeRequest:
            path = 'foo'
        request = FakeRequest()
        class FakeReply:
            headers = http.HTTPHeaders()
        reply = FakeReply()
    
        coll = StaticCollection()
        coll.bind('foo/bar', gadget)
        
        self.assertRaises(error.web.Moved, coll.handle, request, reply, 'foo')
        self.assertEquals(reply.headers['location'], 'foo/')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(StaticCollectionTestCase, 'test')])
suite.addTests([unittest.makeSuite(FilesystemCollectionTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)