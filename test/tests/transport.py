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
