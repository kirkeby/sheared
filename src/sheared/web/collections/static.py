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

from sheared import error
from sheared.web.collections.collection import Collection

class StaticCollection(Collection):
    def __init__(self):
        Collection.__init__(self)

        self.bindings = {}
        self.index = 'index'

    def bind(self, name, thing):
        if '/' in name:
            child, subpath = name.split('/', 1)
            if self.bindings.has_key(child):
                assert isinstance(self.bindings[child], StaticCollection)
            else:
                self.bindings[child] = StaticCollection()
            self.bindings[child].bind(subpath, thing)
        else:
            assert not self.bindings.has_key(name)
            self.bindings[name] = thing

    def lookup(self, name):
        if '/' in name:
            child, subpath = name.split('/', 1)
            return self.bindings[child].lookup(subpath)
        else:
            return self.bindings[name]

    def getChild(self, request, reply, subpath):
        if not subpath:
            subpath = self.index
        if not self.bindings.has_key(subpath):
            raise error.web.NotFoundError
        return self.bindings[subpath]

