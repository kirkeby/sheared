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

from sheared.web import entwiner
from sheared import error

from tests.web import FakeReply, FakeRequest

class EntwinerTestCase(unittest.TestCase):
    def testTemplatePage(self):
        class Foo(entwiner.Entwiner):
            template_page = './test/http-docroot/foo.html'
            def entwine(self, request, reply, subpath):
                self.context['foo'] = 'foo'
        ent = Foo()
        req = FakeRequest()
        rep = FakeReply()
        ent.handle(req, rep, None)
        self.assertEquals(rep.sent, 'foo\n')

    def testTemplatePages(self):
        class Foo(entwiner.Entwiner):
            template_pages = ['./test/http-docroot/foo.html']
            def entwine(self, request, reply, subpath):
                self.context['foo'] = 'foo'
        ent = Foo()
        req = FakeRequest()
        rep = FakeReply()
        ent.handle(req, rep, None)
        self.assertEquals(rep.sent, 'foo\n')

    def testRequestContext(self):
        class FooEntwiner(entwiner.Entwiner):
            template_page = './test/http-docroot/foo.html'
            def entwine(self, request, reply, subpath):
                pass

        request = FakeRequest('/')
        request.context = {'foo': 'fubar'}
        reply = FakeReply()

        foo = FooEntwiner()
        foo.handle(request, reply, '')
        
        self.assertEquals(reply.sent, 'fubar\n')

    def testConditionalGet(self):
        class FooEntwiner(entwiner.Entwiner):
            template_page = './test/http-docroot/foo.html'
            def entwine(self, request, reply, subpath):
                pass

        # test with no match
        request = FakeRequest('/')
        request.context = {'foo': 'fubar'}
        request.headers.setHeader('If-None-Match', 'abc')
        reply = FakeReply()

        foo = FooEntwiner()
        foo.handle(request, reply, '')
        
        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.sent, 'fubar\n')

        # test with match
        request.headers.setHeader('If-None-Match', reply.headers['ETag'])
        reply = FakeReply()

        self.assertRaises(error.web.NotModified, foo.handle, request, reply, '')
        self.assertEquals(reply.sent, '')


suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(EntwinerTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
        
