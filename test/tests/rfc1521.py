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

from sheared.python import rfc1521

class ParseContentTypeTestCase(unittest.TestCase):
    def testEmpty(self):
        "Test parse_content_type with an empty string."
        self.assertRaises(ValueError, rfc1521.parse_content_type, '')
    def testNoSubtype(self):
        "Test parse_content_type with an empty subtype."
        self.assertRaises(ValueError, rfc1521.parse_content_type, 'text')
    def testNoType(self):
        "Test parse_content_type with an empty type."
        self.assertRaises(ValueError, rfc1521.parse_content_type, '/plain')
    def testParamsOnly(self):
        "Test parse_content_type with only parameters."
        self.assertRaises(ValueError, rfc1521.parse_content_type, ';q=1.0')

    def testSimple(self):
        "Test parse_content_type with a simple text/plain content-type."
        self.assertEquals(rfc1521.parse_content_type('text/plain'),
                          ('text/plain', {}))

    def testWithParams(self):
        "Test parse_content_type with a content-type with parameters."
        self.assertEquals(rfc1521.parse_content_type('text/plain ;q=1;v=2'),
                          ('text/plain', {'q': '1', 'v': '2'}))

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(ParseContentTypeTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
