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
