import unittest
import encoding

class EncodeTestCase(unittest.TestCase):
    def testUTF8(self):
        self.assertEquals(encoding.utf8.encode(u'utf-8'),
                          'utf-8')

class DecodeTestCase(unittest.TestCase):
    def testUTF8(self):
        self.assertEquals(encoding.utf8.decode('utf-8'),
                          u'utf-8')

if __name__ == '__main__':
    unittest.main()

