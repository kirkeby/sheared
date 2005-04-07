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

from sheared.database import pool
from sheared.database import dummy

class DatabaseConnectionPoolTestCase(unittest.TestCase):
    def setUp(self):
        self.pool = pool.DatabaseConnectionPool(self.factory)
    def factory(self):
        return dummy.DummyDatabaseClient()

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

if __name__ == '__main__':
    try:
        import stackless
    except:
        stackless = None

    if not stackless is None:
        unittest.main()
