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

from sheared import error

from sheared.web.resource import MovedResource, AliasedResource
from sheared.web.collections.static import StaticCollection
from sheared.web.virtualhost import VirtualHost

from web import FakeRequest, FakeReply, FakeResource

class MovedResourceTestCase(unittest.TestCase):
    def testShallow(self):
        request = FakeRequest('GET /foo HTTP/1.0')
        reply = FakeReply()

        coll = MovedResource('bar')
        self.assertRaises(error.web.MovedPermanently, coll.handle,
                          request, reply, '')
        self.assertEquals(reply.headers['location'], 'bar')

    def testDeep(self):
        request = FakeRequest('GET /fubar HTTP/1.0')
        reply = FakeReply()

        coll = MovedResource('fu')
        coll = coll.getChild(request, reply, 'bar')
        self.assertRaises(error.web.MovedPermanently, coll.handle,
                          request, reply, '')
        self.assertEquals(reply.headers['location'], 'fu/bar')

class AliasedResourceTestCase(unittest.TestCase):
    def testGet(self):
        request = FakeRequest('GET /alias HTTP/1.0')
        reply = FakeReply()

        orig = FakeResource()
        alias = AliasedResource(orig, 'real')
        coll = StaticCollection()
        coll.bind('real', orig)
        coll.bind('alias', alias)
        vh = VirtualHost(coll)

        vh.handle(request, reply)
        
        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.headers.has_key('Location'), 1)
        self.assertEquals(reply.headers['Location'], 'real')
        self.assertEquals(reply.headers['Content-Type'], 'text/plain')
        self.assertEquals(reply.sent, 'Welcome to foo!\r\n')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(AliasedResourceTestCase, 'test')])
suite.addTests([unittest.makeSuite(MovedResourceTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
