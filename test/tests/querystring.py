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

from sheared import error

from sheared.web import querystring

class HTTPQueryStringTestCase(unittest.TestCase):
    def setUp(self):
        qs = 'int=1&hex=babe&str=foo&flag&many=1&many=2'
        self.qs = querystring.HTTPQueryString(qs)

    def testGetOne(self):
        self.assertEquals(self.qs.get_one('int').as_name(), '1')
        self.assertEquals(self.qs.get_one('hex').as_name(), 'babe')
        self.assertEquals(self.qs.get_one('str').as_name(), 'foo')
        self.assertRaises(error.web.InputError, self.qs.get_one, 'flag')
        self.assertRaises(error.web.InputError, self.qs.get_one, 'many')

    def testGetMany(self):
        self.assertEquals(len(self.qs.get_many('int')), 1)
        self.assertEquals(len(self.qs.get_many('hex')), 1)
        self.assertEquals(len(self.qs.get_many('str')), 1)
        self.assertEquals(len(self.qs.get_many('flag')), 0)
        self.assertEquals(len(self.qs.get_many('many')), 2)

    def testHasKey(self):
        self.assertEquals(self.qs.has_key('int'), 1)
        self.assertEquals(self.qs.has_key('hex'), 1)
        self.assertEquals(self.qs.has_key('str'), 1)
        self.assertEquals(self.qs.has_key('flag'), 1)
        self.assertEquals(self.qs.has_key('many'), 1)
        self.assertEquals(self.qs.has_key('1'), 0)
        self.assertEquals(self.qs.has_key('foo'), 0)
        self.assertEquals(self.qs.has_key('babe'), 0)
        self.assertEquals(self.qs.has_key('other'), 0)

class UnvalidatedInputTestCase(unittest.TestCase):
    def setUp(self):
        self.int = querystring.UnvalidatedInput('a', '1')
        self.hex = querystring.UnvalidatedInput('b', 'babe')
        self.str = querystring.UnvalidatedInput('c', 'foo')

    def testInteger(self):
        self.assertEquals(self.int.as_int(), 1)
        self.assertEquals(self.hex.as_int(16), 0xBABE)
        self.assertEquals(self.hex.as_name(), 'babe')
        self.assertRaises(error.web.InputError, self.str.as_int)

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(HTTPQueryStringTestCase, 'test')])
suite.addTests([unittest.makeSuite(UnvalidatedInputTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
