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
from sheared.web import resource

class Collection(resource.GettableResource):
    def getChild(self, request, reply, subpath):
        raise NotImplementedError

    def handle(self, request, reply, subpath):
        if request.path.endswith('/'):
            self.getChild(request, reply, '').handle(request, reply, subpath)
        else:
            reply.headers.setHeader('Location', request.path + '/')
            raise error.web.MovedPermanently
