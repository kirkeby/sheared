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

from sheared.protocol import http

class HTTPDateTimeTestCase(unittest.TestCase):
    def testUnixtime(self):
        """Test HTTPDateTime against unixtime (seconds since epoch)."""
        d = http.HTTPDateTime(300229200)
        self.assertEquals(str(d), "Sat, 07 Jul 1979 21:00:00 GMT")

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

    def testComparison(self):
        s = http.HTTPDateTime(300000000)
        t = http.HTTPDateTime(300229200)
        u = http.HTTPDateTime(300300000)

        self.assertEquals(s < t, 1)
        self.assertEquals(t < u, 1)
        self.assertEquals(s < u, 1)

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
        # Should we be white-space preserving?
        #h = http.HTTPHeaders("Header: value ")
        #self.assertEquals(h['header'], 'value ')
        #h = http.HTTPHeaders("Header:  value")
        #self.assertEquals(h['header'], ' value')

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

        h = http.HTTPHeaders("Header: value, and this too")
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
        # XMMS breaks this :(
        #self.assertRaises(ValueError, http.HTTPHeaders, "Header:")
        self.assertRaises(ValueError, http.HTTPHeaders, "\r\n Header: bar")

    def testKeys(self):
        """Test HTTPHeaders.keys."""
        h = http.HTTPHeaders("Foo: value\r\nBar: and this too")
        self.assertEquals(h.keys(), ['Foo', 'Bar'])

    def testDel(self):
        """Test HTTPHeaders.delHeader."""
        h = http.HTTPHeaders("Foo: value\r\nBar: and this too")
        h.delHeader('Bar')
        self.assertEquals(h.keys(), ['Foo'])

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

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPDateTimeTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPHeadersTestCase, 'test')])
suite.addTests([unittest.makeSuite(HTTPRequestLineTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
