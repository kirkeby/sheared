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
import warnings

from entwine import entwine

from sheared.python import io
from sheared.web import resource

class Entwiner(resource.NormalResource):
    def __init__(self):
        resource.NormalResource.__init__(self)

    def handle(self, request, reply, subpath):
        self.context = {}
        self.entwine(request, reply, subpath)
        r = self.execute(self.page_path, throwaway=0)
        reply.send(r)

    def execute(self, path, throwaway=1):
        r = entwine(io.readfile(path), self.context)

        if throwaway and r.strip():
            warnings.warn('%s: ignored non-macro content' % path)

        return r