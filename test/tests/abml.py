# vim:nowrap:textwidth=0

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

