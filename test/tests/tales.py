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

from dtml import tales
from dtml import context

# FIXME -- need separate testcases for context, compiler and interpreter

class TALESContextTestCase(unittest.TestCase):
    def testFoo(self):
        self.context = context.Context()
        self.context.setGlobal('author', {'name': 'Sune Kirkeby'})
        self.context.setGlobal('year', 2001)
        self.context.setGlobal('now', 'just this minute')

        # FIXME -- this can't be done?!?
        #self.interpreter = tales.Interpreter(self.context)

class TALESInterpreterTestCase(unittest.TestCase):
    def setUp(self):
        self.context = context.Context()
        self.context.setGlobal('author', {'name': 'Sune Kirkeby'})
        self.context.setGlobal('year', 2001)
        self.context.setGlobal('now', 'just this minute')

    def execute(self, text):
        return tales.execute(tales.compile(text), self.context)

    def testString(self):
        """Test with a simple string (ie. no variable interpolation)."""
        self.assertEquals(self.execute('string:Foo, inc.'), 'Foo, inc.')

    def testStringDollarDollar(self):
        """Test a string:expresion containing '$$'."""
        self.assertEquals(self.execute('string:$$'), '$')
        self.assertEquals(self.execute('string:$${now}'), '${now}')

    def testStringDollarDollarDollar(self):
        """Test with a string containing $$ and a variable interpolation."""
        self.assertEquals(self.execute('string:$$${now}'), '$just this minute')

    def testStringInterpolation(self):
        """Test with a string containing variable interpolation."""
        self.assertEquals(self.execute('string:Copyright &copy; ${author/name}, $year'), 'Copyright &copy; Sune Kirkeby, 2001')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(TALESInterpreterTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
