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

import re

from sheared import error

def unscape_querystring(qs):
    qs = qs.replace('+', ' ')
    while 1:
        try:
            before, after = qs.split('%', 1)
        except ValueError:
            break

        if len(after) < 2:
            raise error.web.InputError, (None, 'percent near end of query-string')
        hex, after = after[0:2], after[2:]
        if re.findall('[^0-9a-fA-F]', hex):
            raise error.web.InputError, (None, 'malformed hex-number in query-string')
        qs = before + chr(int(hex, 16)) + after
    return qs

def parse_querystring(qs):
    args = {}
    if not len(qs):
        return args
    for part in qs.split('&'):
        thing = map(unscape_querystring, part.split('=', 1))
        if len(thing) == 1:
            thing = thing[0], ''
        name, value = thing
        if len(name) == 0:
            raise error.web.InputError, (None, 'zero-length name not allowed')
        if re.findall('[^a-zA-Z0-9-_]', name):
            raise error.web.InputError, (None, 'invalid name in query-string')
        if not args.has_key(name):
            args[name] = []
        if len(value):
            args[name].append(UnvalidatedInput(name, value))
    return args

class UnvalidatedInput:
    def __init__(self, name, str):
        self.name = name
        self.__str = str

    def as_int(self, radix=10):
        try:
            return int(self.__str, radix)
        except ValueError:
            raise error.web.InputError, (self.name, 'invalid integer')

    def as_float(self):
        try:
            return float(self.__str)
        except ValueError:
            raise error.web.InputError, (self.name, 'invalid floateger')

    def as_bool(self):
        return bool(self.__str)
    
    def as_str(self, valid):
        if re.findall('[^%s]' % valid, self.__str):
            raise error.web.InputError, (self.name, 'invalid characters in value')
        return self.__str

    def as_unixstr(self):
        return self.as_str('\x01-\xff')

    def as_name(self):
        return self.as_str('a-zA-Z0-9:_-')

    def as_word(self):
        return self.as_str('\x21-\x7e')

    def as_text(self):
        return self.as_str('\t\n\r\x20-\x7e')
    
class HTTPQueryString:
    def __init__(self, qs):
        self.dict = parse_querystring(qs)

    def get_one(self, name, *default):
        assert len(default) <= 1
        v = self.get_many(name, list(default))
        if len(v) == 0 and default:
            v = UnvalidatedInput(name, default[0])
        elif len(v) == 1:
            v = v[0]
        else:
            raise error.web.InputError, '%s: expected scalar-arg, ' \
                                             'got %r' % (name, v)
        return v

    def get_many(self, name, default=None):
        try:
            return self.dict[name]
        except KeyError:
            if default is None:
                raise error.web.InputError, '%s: required argument missing' % name
            else:
                return map((lambda v: UnvalidatedInput(name, v)), default)

__all__ = ['HTTPQueryString']
