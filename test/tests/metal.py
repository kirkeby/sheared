# vim:nowrap:textwidth=0

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

