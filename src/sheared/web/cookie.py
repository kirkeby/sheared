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

import time
import types

from sheared.web import querystring

class Cookie:
    def __init__(self, name, value, expires=None, domain=None,
                 path=None, secure=None):
        assert type(name) is types.StringType
        assert type(value) is types.StringType

        self.name = name
        self.value = value
        self.expires = expires
        self.domain = domain
        self.path = path
        self.secure = secure

good_chars = []
good_chars.extend([chr(o) for o in range(ord('a'), ord('z') + 1)])
good_chars.extend([chr(o) for o in range(ord('A'), ord('Z') + 1)])
good_chars.extend([chr(o) for o in range(ord('0'), ord('9') + 1)])
def quote(str):
    q_str = ''
    for ch in str:
        if ch in good_chars:
            q_str = q_str + ch
        else:
            q_str = q_str + ('%%%02x' % ord(ch))
    return q_str
def unquote(q_str):
    return querystring.unscape_querystring(q_str)
        
def parse(str):
    kwargs = {}

    parts = str.split(';')
    
    part = parts.pop(0)
    name, value = part.split('=')
    kwargs['name'] = unquote(name)
    kwargs['value'] = unquote(value)
    
    for part in parts:
        name, value = part.split('=')
        name = name.strip()
        value = value.strip()
    
        kwargs[name] = value

    if kwargs.get('expires', ''):
        kwargs['expires'] = time.mktime(
                time.strptime(kwargs['expires'],
                              "%A, %d-%b-%Y %H:%M:%S GMT"))

    return Cookie(**kwargs)

def format(cookie):
    str = '%s=%s' % (quote(cookie.name), quote(cookie.value))
    if not cookie.expires is None:
        str = str + ('; expires=%s'
                     % time.strftime("%A, %d-%b-%Y %H:%M:%S GMT",
                                     time.gmtime(cookie.expires)))
    if cookie.domain:
        str = str + ('; domain=%s' % cookie.domain)
    if cookie.path:
        str = str + ('; path=%s' % cookie.path)
    if cookie.secure:
        str = str + '; secure'
    return str

__all__ = ['Cookie', 'parse', 'format']
