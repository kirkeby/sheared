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

from __future__ import generators

def parseHeaderLines(s):
    lines = []
    physical = s.split('\r\n')
    for line in physical:
        if line == '':
            continue
        if line[0] in '\t ':
            if not lines:
                raise ValueError('first line cannot be a continued line')
            lines[-1] = lines[-1] + line
        else:
            lines.append(line)

    for line in lines:
        yield parseHeaderLine(line)

def parseHeaderLine(s):
    try:
        name, value = s.split(':', 1)
        if not name:
            raise ValueError
        name = name.strip()
        value = value.strip()
    except ValueError:
        raise ValueError('"%s" is not a proper RFC 822 header' % s)
    return name, value

class RFC822Headers:
    def __init__(self, s=None):
        self.order = []
        self.headers = {}
        if not s is None:
            for name, value in parseHeaderLines(s):
                self.addHeader(name, value)

    def headerKey(self, n):
        return n.lower()

    def addHeader(self, name, value):
        key = self.headerKey(name)
        if not self.headers.has_key(key):
            self.setHeader(name, value)
        else:
            self.headers[key][1].append(value)
    
    def setHeader(self, name, value):
        key = self.headerKey(name)
        if not self.headers.has_key(key):
            self.order.append(name)
        self.headers[key] = (name, [value])
        
    def get(self, name, *argv):
        assert len(argv) < 2, 'get takes one or two arguments'

        if self.headers.has_key(self.headerKey(name)):
            return self.headers[self.headerKey(name)][1]
        elif len(argv):
            return argv[0]
        else:
            raise KeyError, name
    def __getitem__(self, name):
        return self.get(name)
    def has_key(self, name):
        return self.headers.has_key(self.headerKey(name))
    def item(self, name):
        return name, self.get(name)
    def items(self):
        return map(self.item, self.order)

class RFC822Message:
    def __init__(self, s=None):
        if s:
            h, b = s.split('\r\n\r\n', 1)
            self.headers = RFC822Headers(h)
            self.body = b
        else:
            self.headers = RFC822Headers()
            self.body = ''

__all__ = ['RFC822Headers', 'RFC822Message']
