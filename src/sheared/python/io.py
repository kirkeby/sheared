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
from __future__ import generators

from sheared import reactor

def readfile(path):
    f = reactor.open(path, 'r')
    return f.read()

class BufferedReader:
    def __init__(self, file):
        self.file = file
        self.other = getattr(file, 'other', None)
        self.buffer = ''

    def read(self, max=None):
        if max is None:
            d = self.buffer + self.file.read()
            self.buffer = ''
            return d
            
        while len(self.buffer) < max:
            got = self.file.read(max - len(self.buffer))
            if got == '':
                break
            self.buffer = self.buffer + got

        if max > len(self.buffer):
            got, self.buffer = self.buffer, ''
        else:
            got = self.buffer[:max]
            self.buffer = self.buffer[max:]

        return got

    def readline(self, nl='\r\n'):
        # FIXME -- default nl value should be '\n'
        while 1:
            i = self.buffer.find(nl)
            if i >= 0:
                break

            got = self.file.read(80)
            if got == '':
                break
            self.buffer = self.buffer + got
        
        if i < 0:
            got, self.buffer = self.buffer, ''
        else:
            got = self.buffer[ : i + len(nl)]
            self.buffer = self.buffer[i + len(nl) : ]

        return got

    def readlines(self, nl='\n'):
        while 1:
            l = self.readline(nl)
            if l == '':
                break
            yield l

    def write(self, data):
        self.file.write(data)
    def sendfile(self, file):
        self.file.sendfile(file)
    def fileno(self):
        return self.file.fileno()
    def close(self):
        self.file.close()
