# vim:nowrap:textwidth=0

import unittest

from sheared import reactor
from sheared.python import coroutine
from sheared.protocol import postgresql

class DatabaseClientTestCase(unittest.TestCase):
    def setUp(self):
        self.reactor = reactor
        self.reactor.reset()

    def testSelect(self):
        def foo(reactor, protocol):
            connection = reactor.connectTCP(protocol, ('127.0.0.1', 5432), user='sune')
            result = connection.query('SELECT * FROM test')
            return result
        co = coroutine.Coroutine(foo)
        self.reactor.addCoroutine(co, (self.reactor, self.protocol))
        self.reactor.run()

        self.failUnless(hasattr(co, 'result'))
        self.assertEquals(len(co.result[0]), 2)
        self.assertEquals(len(co.result[1]), 3)

class PostgresqlClientTestCase(DatabaseClientTestCase):
    protocol = postgresql.PostgresqlClient

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(PostgresqlClientTestCase, "test")])

__all__ = ['suite']
