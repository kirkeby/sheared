# vim:nowrap:textwidth=0

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

        self.interpreter = tales.Interpreter(self.context)

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
