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

import stackless

from sheared import reactor

from sheared.python.log import Log
from sheared.python.semaphore import Semaphore

class LogFile(Log):
    def __init__(self, path):
        self.path = path
        self.file = None
        self.sem = Semaphore()

    def open(self):
        self.close()
        self.file = reactor.open(self.path, 'w')
        self.file.seek(0, 2)

    def close(self):
        if self.file:
            self.file.close()
            self.file = None

    def write(self, s):
        if not self.file:
            self.open()

        self.sem.grab()
        self.file.write(s)
        self.sem.release()

__all__ = ['LogFile']
