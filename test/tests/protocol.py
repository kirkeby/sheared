#!/usr/bin/env python

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
