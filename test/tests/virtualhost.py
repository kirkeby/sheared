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

from sheared.web.virtualhost import VirtualHost
from sheared import error

from tests.web import FakeRequest, FakeReply, SimpleCollection

class VirtualHostTestCase(unittest.TestCase):
    def setUp(self):
        coll = SimpleCollection('foo')
        self.virtualhost = VirtualHost(coll)
    
    def testNormalGet(self):
        request = FakeRequest('GET / HTTP/1.0')
        reply = FakeReply()
        self.virtualhost.handle(request, reply)
        self.assertEquals(reply.status, 200)
        self.assertEquals(reply.sent, 'Welcome to foo!\r\n')

    def testRedirectWithoutHostHeader(self):
        request = FakeRequest('GET /moved HTTP/1.0')
        reply = FakeReply()
        self.assertRaises(error.web.Moved,
                          self.virtualhost.handle, request, reply)
        self.assertEquals(reply.headers['Location'], '/')

    def testRedirectWithHostHeader(self):
        request = FakeRequest('GET /moved HTTP/1.0', 'Host: foo.com\r\n')
        reply = FakeReply()
        self.assertRaises(error.web.Moved,
                          self.virtualhost.handle, request, reply)
        self.assertEquals(reply.headers['Location'], 'http://foo.com/')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(VirtualHostTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
