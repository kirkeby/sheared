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

import unittest, random

from sheared.web import virtualhost
from sheared.web import client
from sheared.web import server
from sheared import reactor

import tests.web

class GetContentTestCase(unittest.TestCase):
    def setUp(self):
        self.port = int(random.random() * 8192 + 22000)

        coll = tests.web.SimpleCollection('localhost')
        vhost = virtualhost.VirtualHost(coll)
        srv = server.HTTPServer()
        srv.addVirtualHost('localhost', vhost)
        srv.setDefaultHost('localhost')

        reactor.listenTCP(srv, ('127.0.0.1', self.port),
                          max_client_count=1)

    def runGetContent(self):
        content = client.get_content('http://127.0.0.1:%d/' % (self.port))
        self.assertEquals(content, 'Welcome to localhost!\r\n')

    def testGetContent(self):
        reactor.createtasklet(self.runGetContent)
        reactor.start()

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(GetContentTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
