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
from sheared.python import queue

class DatabaseConnection:
    def __init__(self, real, pool):
        self.pool = pool
        self.real = real

        self.query = real.query
        
        self.begin = real.begin
        self.commit = real.commit
        self.rollback = real.rollback

        self.quote_str = real.quote_str
        self.quote_name = real.quote_name
        self.quote_bool = real.quote_bool

    def __del__(self):
        self.pool.releaseConnection(self.real)

class DatabaseConnectionPool:
    def __init__(self, factory, max=4):
        self.factory = factory
        self.max = max

        self.connected = []
        self.available = queue.StacklessQueue()

    def borrow(self):
        return DatabaseConnection(self.leaseConnection(), self)

    def leaseConnection(self):
        if (len(self.available) == 0) and (len(self.connected) < self.max):
            conn = self.factory()
            self.connected.append(conn)
        else:
            conn = self.available.dequeue()

        return conn

    def releaseConnection(self, conn):
        assert conn in self.connected
        self.available.enqueue(conn)

    def query(self, sql):
        conn = self.leaseConnection()
        try:
            return conn.query(sql)
        finally:
            self.releaseConnection(conn)
