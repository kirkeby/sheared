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

import random, os, types

class StringTransport:
    def __init__(self):
        self.input = ''
        self.output = ''
        self.closed = 0

    def read(self, cnt=4096):
        cnt = min(cnt, 1 + int(random.random() * (len(self.input) - 1)))
        data = self.input[:cnt]
        self.input = self.input[cnt:]
        return data

    def write(self, data):
        if self.closed:
            raise IOError, 'cannot write to a closed Transport'
        self.output = self.output + data
        return len(data)

    def sendfile(self, file):
        d = file.read()
        while not d == '':
            self.output = self.output + d
            d = file.read()

    def close(self):
        if self.closed:
            raise IOError, 'already closed'
        self.closed = 1

    def appendInput(self, data):
        self.input = self.input + data
    def getOutput(self):
        return self.output

class FileTransport:
    def __init__(self, file):
        self.file = file
        if isinstance(file, types.IntType):
            self.fileno = file
        else:
            self.fileno = file.fileno()

    def read(self, max=4096):
        return os.read(self.fileno, max)
    def write(self, data):
        while data:
            cnt = os.write(self.fileno, data)
            data = data[cnt:]
    def close(self):
        self.file.close()
