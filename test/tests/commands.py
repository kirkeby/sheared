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

from sheared import reactor
from sheared.python import commands

class GetoutputTestCase(unittest.TestCase):
    def testTrue(self):
        """Test getoutput against /bin/true."""
        def run():
            reactor.result = commands.getoutput('/bin/true', ['true'])
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, '')

    def testFalse(self):
        """Test getoutput against /bin/false."""
        def run():
            reactor.result = commands.getoutput('/bin/false', ['false'])
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, '')

    def testStdout(self):
        """Test getoutput against a program making output to stdout."""
        def run():
            argv = ['/bin/sh', '-c', 'echo Hello, World > /dev/stdout']
            reactor.result = commands.getoutput(argv[0], argv)
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, 'Hello, World\n')

    def testStderr(self):
        """Test getoutput against a program making output to stderr."""
        def run():
            argv = ['/bin/sh', '-c', 'echo Hello, World > /dev/stderr']
            reactor.result = commands.getoutput(argv[0], argv)
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, 'Hello, World\n')

class GetstatusoutputTestCase(unittest.TestCase):
    def testTrue(self):
        """Test getoutput against /bin/true."""
        def run():
            reactor.result = commands.getstatusoutput('/bin/true', ['true'])
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, (0, ''))

    def testFalse(self):
        """Test getstatusoutput against /bin/false."""
        def run():
            reactor.result = commands.getstatusoutput('/bin/false', ['false'])
        reactor.createtasklet(run)
        reactor.start()
        self.assertNotEquals(reactor.result, (0, ''))

    def testStdout(self):
        """Test getstatusoutput against a program making output to stdout."""
        def run():
            argv = ['/bin/sh', '-c', 'echo Hello, World > /dev/stdout']
            reactor.result = commands.getstatusoutput(argv[0], argv)
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, (0, 'Hello, World\n'))

    def testStderr(self):
        """Test getstatusoutput against a program making output to stderr."""
        def run():
            argv = ['/bin/sh', '-c', 'echo Hello, World > /dev/stderr']
            reactor.result = commands.getstatusoutput(argv[0], argv)
        reactor.createtasklet(run)
        reactor.start()
        self.assertEquals(reactor.result, (0, 'Hello, World\n'))

class SpawnTestCase(unittest.TestCase):
    def tearDown(self):
        if hasattr(self, 'result'):
            del self.result
        if hasattr(self, 'error'):
            del self.error

    def testCatDevNull(self):
        def run():
            argv = ['/bin/cat', '/dev/null']
            pid, stdin, stdout = commands.spawn(argv[0], argv)
            stdin.close()
            self.result = stdout.read() ; stdout.close()

        reactor.createtasklet(run)
        reactor.start()

        self.assertEquals(self.result, '')

    def testCatDevNullWithStderr(self):
        def run():
            argv = ['/bin/cat', '/dev/null']
            pid, stdin, stdout, stderr = commands.spawn(argv[0], argv, with_stderr=1)
            stdin.close()
            self.result = stdout.read() ; stdout.close()
            self.error = stderr.read() ; stderr.close()

        reactor.createtasklet(run)
        reactor.start()

        self.assertEquals(self.result, '')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(GetoutputTestCase, 'test')])
suite.addTests([unittest.makeSuite(GetstatusoutputTestCase, 'test')])
suite.addTests([unittest.makeSuite(SpawnTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
