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

import re
from sheared.database import error

class DummyRowDescription:
    def __init__(self, name, type, len):
        self.name = name
        self.type = type
        self.len = len

class DummyCursor:
    def __init__(self, description, rows):
        self.description = description
        self.rows = rows
        self.cursor = 0

    def fetchone(self):
        if self.cursor is None:
            raise error.ProgrammingError, 'cursor has been released'
        if self.cursor == len(self.rows):
            raise error.CursorEmpty, 'no more rows in cursor'
        c, self.cursor = self.cursor, self.cursor + 1
        return self.rows[c]

    def fetchall(self):
        if self.cursor is None:
            raise error.ProgrammingError, 'cursor has been released'
        rows = self.rows[self.cursor:]
        self.cursor = len(self.rows)
        return rows

    def release(self):
        if self.cursor is None:
            raise error.ProgrammingError, 'cursor already released'
        self.rows = None
        self.columns = None
        self.cursor = None

class DummyDatabaseClient:
    def __init__(self):
        self.test = {'0': '', '1': '', '42': 'The Answer'}
        self.work = None

    def begin(self):
        if not self.work is None:
            raise error.ProgrammingError, 'already in transaction'
        self.work = {}
        self.work.update(self.test)
    def commit(self):
        if self.work is None:
            raise error.ProgrammingError, 'not in transaction'
        self.test = self.work
        self.work = None
    def rollback(self):
        if self.work is None:
            raise error.ProgrammingError, 'not in transaction'
        self.work = None

    def close(self):
        if not self.work is None:
            raise error.ProgrammingError, 'cannot close in midst of transaction'
        pass

    def query(self, sql):
        if sql == 'SELECT * FROM test':
            if self.work is None:
                return DummyCursor(('id', 'value'), self.test.items())
            else:
                return DummyCursor(('id', 'value'), self.work.items())
        elif sql == 'DELETE FROM test WHERE id=1':
            if self.work is None:
                raise error.ProgrammingError, 'not in transaction'
            if self.work.has_key('1'):
                del self.work['1']
                return 1 # or None, if we do not know
            else:
                return None # or 0, if we do know
        elif sql == 'SELECT * FROM test WHERE id=7':
            return DummyCursor(('id', 'value'), [])
        elif sql == 'CREATE TABLE test (id int)':
            raise error.ProgrammingError, 'table test already exists'
        elif sql == 'CREATE TABLE test2 (id int)':
            self.test2 = {}
        elif sql == 'DROP TABLE test2':
            delattr(self, 'test2')
        else:
            raise error.InterfaceError, 'sorry, I am just a dumb database backend.'
