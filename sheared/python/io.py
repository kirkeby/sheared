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
from sheared import reactor

def readfile(path):
    if reactor.running:
        f = reactor.open(path, 'r')
    else:
        f = open(path, 'r')
    return readall(f)

def readall(f):
    all = ''
    while 1:
        read = f.read()
        if read == '':
            break
        all += read
    return all

class BufferedReader:
    def __init__(self, file):
        self.file = file
        self.other = getattr(file, 'other', None)
        self.buffer = ''

    def read(self, cnt):
        while len(self.buffer) < cnt:
            got = self.file.read()
            if got == '':
                break
            self.buffer = self.buffer + got

        if cnt > len(self.buffer):
            got, self.buffer = self.buffer, ''
        else:
            got = self.buffer[:cnt]
            self.buffer = self.buffer[cnt:]

        return got

    def readline(self, nl='\r\n'):
        while 1:
            i = self.buffer.find(nl)
            if i >= 0:
                break

            got = self.file.read()
            if got == '':
                break
            self.buffer = self.buffer + got
        
        if i < 0:
            got, self.buffer = self.buffer, ''
        else:
            got = self.buffer[ : i + len(nl)]
            self.buffer = self.buffer[i + len(nl) : ]

        return got

    def write(self, data):
        self.file.write(data)
    def sendfile(self, file):
        self.file.sendfile(file)
    def fileno(self):
        return self.file.fileno()
    def close(self):
        self.file.close()
