# vim:nowrap:textwidth=0

import unittest

from dtml import tal
from dtml import tales
from dtml import context

# FIXME -- we should probably look at the document-tree rather than it's
# textual representation here...
class TALInterpreterTestCase(unittest.TestCase):
    def setUp(self):
        self.context = {
            'nothing': None,
            'default': self,
        }

    def execute(self, xml):
        return tal.execute(tal.compile(xml, tales), self.context, tales)

    def testVanillaXML(self):
        """Test with plain, vanilla XML."""
        self.assertEquals(self.execute('<tag />text'), '<tag />text')

    def testConditionNothing(self):
        """Test tal:condition with nothing as value."""
        self.assertEquals(self.execute('<tag tal:condition="nothing" />'), '')

    def testConditionDefault(self):
        """Test tal:condition with default as value."""
        self.assertEquals(self.execute('<tag tal:condition="default" />'), '<tag></tag>')

    def testAttribute(self):
        """Test tal:attribute."""
        self.assertEquals(self.execute('<tag tal:attributes="src string:foo" />'), "<tag src='foo'></tag>")

    def testContent(self):
        """Test tal:content."""
        self.assertEquals(self.execute('<tag tal:content="string:foo">fugl</tag>'), '<tag>foo</tag>')

    def testReplace(self):
        """Test tal:replace."""
        self.assertEquals(self.execute('<tag tal:replace="string:foo">fugl</tag>'), 'foo')

    def testOmitTag(self):
        """Test tal:omit-tag."""
        self.assertEquals(self.execute('<tag tal:omit-tag="default">content</tag>'), 'content')

    def testOmitTagContent(self):
        """Test tal:omit-tag and tal:content together."""
        self.assertEquals(self.execute('<tag tal:omit-tag="default" tal:content="string:foo">content</tag>'), 'foo')

    def testRepeatEmpty(self):
        """Test tal:repeat."""
        self.assertEquals(self.execute('<tag tal:repeat="item python:[]" tal:omit-tag="default" tal:content="item" />'), '')

    def testRepeatOne(self):
        """Test tal:repeat."""
        self.assertEquals(self.execute('<tag tal:repeat="item python:[1]" tal:omit-tag="default" tal:content="item" />'), '1')

    def testRepeatTwo(self):
        """Test tal:repeat."""
        self.assertEquals(self.execute('<tag tal:repeat="item python:[1, 2]" tal:content="item" />'), '<tag>1</tag><tag>2</tag>')

    def testDefine(self):
        """Test tal:define."""
        self.assertEquals(self.execute('<tag tal:define="foo string:foo" tal:content="foo" />'), '<tag>foo</tag>')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(TALInterpreterTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
