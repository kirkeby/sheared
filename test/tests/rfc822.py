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

from sheared.python import rfc822

class RFC822HeadersTestCase(unittest.TestCase):
    def testEmpty(self):
        """Test RFC822Headers with no headers."""
        h = rfc822.RFC822Headers("")
        self.failIf(len(h.items()))

    def testCase(self):
        """Test RFC822Headers with different cased headers and lookups."""
        h = rfc822.RFC822Headers("Header: value\r\n" + "some-Other-heAder: Some-Other-value\r\n")

        self.failUnless(h.has_key('header'))
        self.failUnless(h.has_key('some-other-header'))

        self.assertEquals(h.get('Header'), ['value'])
        self.assertEquals(h.get('header'), ['value'])
        self.assertEquals(h['Header'], ['value'])
        self.assertEquals(h['header'], ['value'])

        self.assertEquals(h.get('some-other-header'), ['Some-Other-value'])
        self.assertEquals(h.get('SOME-otHer-header'), ['Some-Other-value'])
        self.assertEquals(h['some-OtheR-header'], ['Some-Other-value'])
        self.assertEquals(h['some-other-heAder'], ['Some-Other-value'])

    def testSingleLine(self):
        """Test RFC822Headers with single-line headers."""
        h = rfc822.RFC822Headers("Header: value")
        self.assertEquals(h['header'], ['value'])
        # Should we be white-space preserving?
        #h = http.HTTPHeaders("Header: value ")
        #self.assertEquals(h['header'], 'value ')
        #h = http.HTTPHeaders("Header:  value")
        #self.assertEquals(h['header'], ' value')

    def testMultiLine(self):
        """Test RFC822Headers with multi-line headers."""
        h = rfc822.RFC822Headers("Header: value\r\n\tand this too")
        self.assertEquals(h['header'], ['value\tand this too'])

    def testMultiple(self):
        """Test RFC822Headers with multiple of the same headers."""
        h = rfc822.RFC822Headers("Header: value\r\nHeader: and this too")
        self.assertEquals(len(h['header']), 2)
        self.assertEquals(h['header'][0], 'value')
        self.assertEquals(h['header'][1], 'and this too')

        h = rfc822.RFC822Headers("Header: value, and this too\r\n")
        self.assertEquals(len(h['header']), 2)
        self.assertEquals(h['header'][0], 'value')
        self.assertEquals(h['header'][1], 'and this too')

    def testItems(self):
        """Test RFC822Headers items method."""
        h = rfc822.RFC822Headers('One: \r\nTwo: \r\n')
        self.assertEquals(h.items(), [('One', ['']), ('Two', [''])])

    def testBadHeaders(self):
        """Test RFC822Headers against some bad RFC822 headers."""
        self.assertRaises(ValueError, rfc822.RFC822Headers, " ")
        self.assertRaises(ValueError, rfc822.RFC822Headers, "\r\n Header: bar")

class RFC822MessageTestCase(unittest.TestCase):
    def testEmpty(self):
        """Test RFC822Message with no headers and no body."""
        m = rfc822.RFC822Message("\r\n\r\n")
        self.failIf(len(m.headers.items()))
        self.failIf(len(m.body))

    def testEmptyHead(self):
        """Test RFC822Message with no headers and body."""
        m = rfc822.RFC822Message("\r\n\r\nHello, World!")
        self.failIf(len(m.headers.items()))
        self.assertEquals(m.body, 'Hello, World!')

    def testEmptyBody(self):
        """Test RFC822Message with headers and no body."""
        m = rfc822.RFC822Message("Hello: World\r\n"
                                 "Hi: There\r\n"
                                 "\r\n")
        self.assertEquals(m.headers.items(), [('Hello', ['World']),
                                              ('Hi', ['There'])])
        self.assertEquals(m.body, '')

    def testHeadAndBody(self):
        """Test RFC822Message with headers and body."""
        m = rfc822.RFC822Message("Hello: World\r\n"
                                 "\r\n"
                                 "Hello, World!")
        self.assertEquals(m.headers.items(), [('Hello', ['World'])])
        self.assertEquals(m.body, 'Hello, World!')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(RFC822HeadersTestCase, 'test')])
suite.addTests([unittest.makeSuite(RFC822MessageTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
