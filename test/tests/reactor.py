# First line.
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
# vim:nowrap:textwidth=0

import unittest
import socket, os, time, errno, commands, random
from sheared import reactor

class ReactorTestCaseMixin:
    """Test a reactor."""

    def setUp(self):
        self.reactor = self.klass()

    def testNothingToDo(self):
        """Test that the reactor cleanly exits when there is nothing to do."""
        self.reactor.start()

    def testRead(self):
        """Test reading from an open file."""
        def f():
            f = os.open('test/tests/reactor.py', os.O_RDONLY)
            f = self.reactor.fdopen(f)
            lines = f.read(4096).split('\n')
            self.assertEquals(lines[0], '# First line.')
        self.reactor.createtasklet(f)
        self.reactor.start()
        
    def testBadWrite(self):
        """Test that the reactor works given bad input to write."""
        def f():
            f = self.reactor.open('/dev/null', 'w')
            try:
                f.write(None)
                self.reactor.stop('bad')
            except TypeError:
                self.reactor.stop('ok')
        self.reactor.createtasklet(f)
        self.assertEquals(self.reactor.start(), 'ok')

    def testSeek(self):
        """Test that the reactor can seek in files."""
        def f():
            f = self.reactor.open('/etc/passwd', 'r')
            f.seek(1, 0)
            self.assertEquals(f.read(3), 'oot')
        self.reactor.createtasklet(f)
        self.reactor.start()

    def testImmediateStop(self):
        """Test that the reactor cleanly exits upon an immediate
        stop-command."""
        def f():
            self.reactor.stop(42)
        self.reactor.createtasklet(f)
        self.assertEquals(self.reactor.start(), 42)
        
    def testSleep(self):
        """Test that the reactor can sleep; and does so for the right
        amount of time."""
        def f():
            started = time.time()
            self.reactor.sleep(0.5)
            stopped = time.time()
            if stopped - started >= 0.45:
                self.reactor.stop(42)
            else:
                self.reactor.stop(stopped - started)
        self.reactor.createtasklet(f)
        self.assertEquals(self.reactor.start(), 42)

    def testListenTCP(self):
        """Test that accepting network connections works properly."""
        port = int(random.random() * 8192 + 22000)
        class Server:
            def startup(self, transport):
                transport.close()
        def f():
            t = reactor.connectTCP(('localhost', port))
            t.close()
            reactor.sleep(0.2)
            t = reactor.connectTCP(('localhost', port))
            t.close()
        reactor.listenTCP(Server(), ('', port), max_client_count=2)
        reactor.createtasklet(f)
        reactor.start()
            
class SelectableReactorTestCase(ReactorTestCaseMixin, unittest.TestCase):
    """Test-cases for the selectable reactor."""
    from sheared.reactors import selectable
    klass = selectable.Reactor

suite = unittest.makeSuite(SelectableReactorTestCase, 'test')

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
