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
    if reactor.current.started and not reactor.current.stopped:
        return reactor_readfile(path)
    else:
        return builtin_readfile(path)
def builtin_readfile(path):
    f = open(path, 'r')
    all = ''
    while 1:
        read = f.read()
        if read == '':
            break
        all += read
    return all
def reactor_readfile(path):
    f = reactor.current.open(path, 'r')
    all = ''
    while 1:
        read = reactor.current.read(f, 4096)
        if read == '':
            break
        all += read
    reactor.current.close(f)
    return all

class Drainer:
    def __init__(self, file):
        self.file = file

    def read(self):
        data = ''
        read = None
        while not read == '':
            read = self.file.read()
            data = data + read
        return data
def readall(file):
    return Drainer(file).read()

class RecordReader:
    def __init__(self, file, newline):
        self.buffered = ''
        self.file = file
        self.newline = newline

    def read(self, max=None):
        if self.buffered:
            if max is None:
                data, self.buffered = self.buffered, ''
            else:
                if len(self.buffered) >= max:
                    data = self.buffered[:max]
                    self.buffered = self.buffered[max:]
                else:
                    data, self.buffered = self.buffered, ''
                    data = data + self.file.read(max - len(data))
        else:
            if max is None:
                data = self.file.read()
            else:
                data = self.file.read(max)
        return data

    def readline(self):
        while self.buffered.find(self.newline) < 0:
            data = self.file.read()
            if data == '':
                break
            self.buffered = self.buffered + data

        i = self.buffered.find(self.newline)
        if i < 0:
            data, self.buffered = self.buffered, ''
        else:
            data = self.buffered[ : i + len(self.newline)]
            self.buffered = self.buffered[i + len(self.newline) : ]
        
        return data
