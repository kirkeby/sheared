# vim:nowrap:textwidth=0

import unittest

from sheared import database

class DatabaseConnectionPoolTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = database.pool.DatabaseConnectionPool(self.factory)
    def factory(self):
        return database.dummy.DummyDatabaseClient()

    def testLease(self):
        leased = self.pool.leaseConnection()
        try:
            result = leased.query("SELECT * FROM test")
            rows = result.fetchall()
            self.assertEquals(len(result.description), 2)
            self.assertEquals(len(rows), 3)
            result.release()
        finally:
            self.pool.releaseConnection(leased)
    
    def testQuery(self):
        result = self.pool.query("SELECT * FROM test")
        rows = result.fetchall()
        self.assertEquals(len(result.description), 2)
        self.assertEquals(len(rows), 3)
        result.release()

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(DatabaseConnectionPoolTestCase, "test")])

__all__ = ['suite']

