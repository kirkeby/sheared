# vim:nowrap:textwidth=0

import unittest, socket, types

from sheared import database
from sheared.reactor import transport

class DatabaseClientTestCase(unittest.TestCase):
    def setUp(self):
        self.connection = self.connect()

    def tearDown(self):
        self.connection.close()
    
    def connectTCP(self, factory, addr, *args, **kwargs):
        sock = socket.socket()
        sock.connect(addr)
        trans = transport.FileTransport(None, sock, addr)
        return apply(factory, (None, trans) + args, kwargs)

    def testOutsideTransaction(self):
        self.assertRaises(database.ProgrammingError, self.connection.commit)
        self.assertRaises(database.ProgrammingError, self.connection.rollback)

    def testDelete(self):
        self.connection.begin()
        try:
            result = self.connection.query('DELETE FROM test WHERE id=1')
            self.failUnless(result is None or isinstance(result, types.IntType))
            result = self.connection.query('DELETE FROM test WHERE id=1')
            self.failUnless(result is None or isinstance(result, types.IntType))
        finally:
            self.connection.rollback()

    def testRollback(self):
        self.connection.begin()
        try:
            self.connection.query('DELETE FROM test WHERE id=1')
            # this test could return a false positive, if the wrong assertion triggers,
            # but I doubt the table schema would change out under us :)
            self.assertRaises(AssertionError, self.testSelect)
        finally:
            self.connection.rollback()
        self.testSelect()

    def testCreateTable(self):
        self.assertRaises(database.ProgrammingError, self.connection.query, 'CREATE TABLE test (id int)')
        self.connection.query('CREATE TABLE test2 (id int)')
        self.connection.query('DROP TABLE test2')

    def testSelect(self):
        result = self.connection.query('SELECT * FROM test')
        rows = result.fetchall()
        self.assertEquals(len(result.description), 2)
        self.assertEquals(len(rows), 3)
        result.release()

class PostgresqlClientTestCase(DatabaseClientTestCase):
    def connect(self):
        return self.connectTCP(database.postgresql.PostgresqlClient, ('127.0.0.1', 5432), user='sune')

class DummyDatabaseClientTestCase(DatabaseClientTestCase):
    def connect(self):
        return database.dummy.DummyDatabaseClient()

def can_connect(port):
    try:
        sock = socket.socket()
        sock.connect(addr)
        sock.close()
        return 1
    except:
        return 0

suite = unittest.TestSuite()
if hasattr(database, 'postgresql') and can_connect(5432):
    suite.addTests([unittest.makeSuite(PostgresqlClientTestCase, "test")])
suite.addTests([unittest.makeSuite(DummyDatabaseClientTestCase, "test")])

__all__ = ['suite']
