# vim:nowrap:textwidth=0

import unittest, os.path, sys

from sheared import reactor
from sheared.reactor import transport

class StringTransportTestCase(unittest.TestCase):
    def testClose(self):
        """Test that a close()d StringTransport raises IOError on read/write/close calls."""
        t = transport.StringTransport()
        t.close()
    
        self.assertRaises(IOError, t.write, '')
        self.assertRaises(IOError, t.close)

    def testRead(self):
        """Test that a StringTransport can be read from."""
        t = transport.StringTransport()
        t.appendInput('Hello, World!')
        d = ''
        while 1:
            r = t.read()
            if r == '':
                break
            d = d + r
        self.assertEquals(d, 'Hello, World!')
        self.assertEquals(t.read(), '')
        t.close()

    def testSmallRead(self):
        """Test that a StringTransport reads in chunks of given maximum."""
        t = transport.StringTransport()
        t.appendInput('Hello, World!')
        d = ''
        while 1:
            r = t.read(1)
            if r == '':
                break
            self.assertEquals(len(r), 1)
            d = d + r
        self.assertEquals(d, 'Hello, World!')
        self.assertEquals(t.read(), '')
        t.close()

    def testWrite(self):
        """Test that a StringTransport can be written to."""
        t = transport.StringTransport()
        t.write('Hello, ')
        t.write('World!')
        t.close()

        self.assertEquals(t.getOutput(), 'Hello, World!')
        
class FileTransportTestCase(unittest.TestCase):
    def testRead(self):
        path = os.path.dirname(sys.argv[0])
        path = '%s/../http-docroot/hello.txt' % path
        t = transport.FileTransport(reactor.current, open(path, 'r'), 'some-file')
        data = ''
        while 1:
            r = t.read()
            if r == '':
                break
            data = data + r
        t.close()
    
        self.assertEquals(data, 'Hello, World!\n')

suite = unittest.makeSuite(StringTransportTestCase, 'test')

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
