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
    physical = s.split('\n')
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
        raise ValueError, '"%s" is not a proper RFC 822 header' % s
    return name, value

class Header:
    def __init__(self, name, value):
        self.name = name
        self.value = value
class RFC822Headers:
    def __init__(self, s=None, canonical=0):
        self.order = []
        self.headers = {}
        if not s is None:
            if not canonical:
                s = s.replace('\r\n', '\n')
            for name, value in parseHeaderLines(s):
                self.addHeader(name, value)

    def headerKey(self, n):
        return n.lower()

    def addHeader(self, name, value):
        key = self.headerKey(name)
        if not self.headers.has_key(key):
            self.setHeader(name, value)
        else:
            self.headers[key].value.append(value)
    def setHeader(self, name, value):
        self._set(name, [value])
    def _set(self, name, value):
        key = self.headerKey(name)
        if not self.headers.has_key(key):
            self.order.append(key)
        self.headers[key] = Header(name, value)
    def delHeader(self, name):
        key = self.headerKey(name)
        del self.headers[key]
        self.order.remove(key)
        
    def get(self, name, *argv):
        assert len(argv) < 2, 'get takes one or two arguments'

        key = self.headerKey(name)
        if self.headers.has_key(key):
            return self.headers[key].value
        elif len(argv):
            return argv[0]
        else:
            raise KeyError, name
    def __getitem__(self, name):
        return self.get(name)
    def has_key(self, name):
        return self.headers.has_key(self.headerKey(name))
    def items(self):
        return [ (self.headers[key].name, self.headers[key].value)
                 for key in self.order ]
    def keys(self):
        return [ self.headers[key].name for key in self.order ]

class RFC822Message:
    def __init__(self, s=None):
        if s:
            h, b = s.replace('\r\n', '\n').split('\n\n', 1)
            self.headers = RFC822Headers(h, canonical=1)
            self.body = b
        else:
            self.headers = RFC822Headers()
            self.body = ''

__all__ = ['RFC822Headers', 'RFC822Message']
