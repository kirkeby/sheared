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

from sheared.python import semaphore
from sheared import reactor

class SemaphoreTestCase(unittest.TestCase):
    def testGrabRelease(self):
        sem = semaphore.Semaphore()
        sem.grab()
        sem.release()

    def testTwoGrabbers(self):
        def grabber(sem):
            sem.grab()
            reactor.sleep(0.3)
            sem.release()
        
        sem = semaphore.Semaphore()
        reactor.createtasklet(grabber, (sem,))
        reactor.createtasklet(grabber, (sem,))
        reactor.start()

suite = unittest.TestSuite()
suite.addTests([unittest.makeSuite(SemaphoreTestCase, 'test')])

__all__ = ['suite']

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
