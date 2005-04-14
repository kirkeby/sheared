# vim:nowrap:textwidth=0
#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby
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

from sheared.python.logfile import LogFile
from sheared import reactor

long_string = 'x' * 32000

def writer(log):
    for i in range(19):
        log.write(long_string)

if __name__ == '__main__':
    import os

    path = '/tmp/sheared.python.logfile.LogFile-test'

    log = LogFile(path)
    for i in range(7):
        reactor.createtasklet(writer, (log,))
    reactor.start()

    os.unlink(path)
