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

from dtml import metal
from dtml import tales
from dtml import context

# FIXME -- we should probably look at the document-tree rather than it's
# textual representation here...
class METALInterpreterTestCase(unittest.TestCase):
    def setUp(self):
        self.builtins = context.BuiltIns({})
        self.context = context.Context()
        self.context.setDefaults(self.builtins)
        self.context.pushContext()

    def execute(self, xml):
        return metal.execute(metal.compile(xml, tales.compile), self.context, self.builtins, tales.execute)

    def testVanillaXML(self):
        """Test with plain, vanilla XML."""
        self.assertEquals(self.execute('<tag />text'),
                                       '<tag />text')

    def testDefineMacro(self):
        """Test with a define-macro but no use-macro."""
        self.assertEquals(self.execute('<tag metal:define-macro="foo">text</tag>'),
                          '')

    def testDefineUseMacro(self):
        """Test with a define-macro followed by a use-macro."""
        self.assertEquals(self.execute('<tag metal:define-macro="foo">text</tag>'
                                       '<tag metal:use-macro="foo" />'),
                                       '<tag>text</tag>')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(METALInterpreterTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()

