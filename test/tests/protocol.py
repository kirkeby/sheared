#!/usr/bin/env python
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
from sheared.reactor import transport
from sheared.python import coroutine
from sheared.protocol import basic
from sheared.protocol import echo

class ProtocolFactoryTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor.current

    def testBuildCoroutine(self):
        """Test that the basic.ProtocolFactory can build Coroutines."""
        f = basic.ProtocolFactory(self.reactor, basic.Protocol)
        t = transport.StringTransport()
        self.failUnless(isinstance(f.buildCoroutine(t), coroutine.Coroutine))

class EchoServerTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor.current.__class__()
        self.protocol = echo.EchoServer
        self.factory = basic.ProtocolFactory(self.reactor, self.protocol)

    def testWithStringTransport(self):
        """Test that the EchoServer works correctly then attached to a StringTransport."""
        t = transport.StringTransport()
        t.appendInput('Hello, World!')
        self.reactor.addCoroutine(self.factory.buildCoroutine(t), ())
        self.reactor.run()
        self.assertEquals(t.getOutput(), 'Hello, World!')

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(ProtocolFactoryTestCase, 'test')])
suite.addTests([unittest.makeSuite(EchoServerTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.main()
