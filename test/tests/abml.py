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

from dtml import abml

class ABMLParseTestCase(unittest.TestCase):
    def testEmpty(self):
        """Test against an empty document."""
        self.assertEquals(list(abml.parse('')), [])

    def testOneTag(self):
        """Test against a document with just one empty tag."""
        self.assertEquals(len(list(abml.parse('<a></a>'))), 2)

    def testSuicidalTag(self):
        """Test against a document with just one empty, suicidal tag."""
        self.assertEquals(len(list(abml.parse('<a />'))), 2)

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(ABMLParseTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()

