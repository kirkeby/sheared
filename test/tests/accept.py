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

from sheared.web import accept
from sheared import error
from tests.web import FakeRequest

class ChooseContentTypeTestCase(unittest.TestCase):
    def testNoAcceptHeader(self):
        request = FakeRequest()
        self.assertEquals('text/html',
                          accept.chooseContentType(request, ['text/html']))

    def testAcceptAnything(self):
        request = FakeRequest()
        request.headers.setHeader('Accept', '*/*')
        self.assertEquals('text/html',
                          accept.chooseContentType(request, ['text/html']))

    def testAcceptWithQval(self):
        request = FakeRequest()
        request.headers.setHeader('Accept', 'text/*; q=0.5, text/html; q=1.0')
        self.assertEquals('text/html',
                          accept.chooseContentType(request,
                            ['text/plain', 'text/html']))

        request.headers.setHeader('Accept', 'text/html, */*; q=0.1')
        self.assertEquals('text/html',
                          accept.chooseContentType(request,
                            ['application/xhtml+xml', 'text/html']))

    def testUnacceptable(self):
        request = FakeRequest()
        request.headers.setHeader('Accept', 'text/plain')
        self.assertRaises(error.web.NotAcceptable,
                          accept.chooseContentType, request, ['text/html'])

    def testCollision(self):
        request = FakeRequest()
        request.headers.setHeader('Accept',
                                  'application/xhtml+xml,text/html')
        self.assertEquals('application/xhtml+xml',
                          accept.chooseContentType(request,
                            ['application/xhtml+xml', 'text/html']))

    def testfudging(self):
        request = FakeRequest()
        request.headers.setHeader('Accept', 'text/html, */*')
        self.assertEquals('text/html',
                          accept.chooseContentType(request,
                              ['application/xhtml+xml', 'text/html']))

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(ChooseContentTypeTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
