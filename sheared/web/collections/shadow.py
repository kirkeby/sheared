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

class ShadowCollection(resource.GettableResource):
    def __init__(self, layers=None):
        resource.GettableResource.__init__(self)

        self.layers = []
        if layers:
            self.layers.extend(layers)

    def addLayer(self, layer):
        self.layers.append(layer)

    def authenticate(self, request, reply):
        for layer in self.layers:
            f = getattr(layer, 'authenticate', None)
            if f:
                f(request, reply)

    def getChild(self, request, reply, subpath):
        lone = None
        children = []
        for layer in self.layers:
            try:
                child = layer.getChild(request, reply, subpath)
                children.append(child)
                if not hasattr(child, 'getChild'):
                    lone = child
            except error.web.NotFoundError:
                pass

        if len(children) == 0:
            raise error.web.NotFoundError
        elif len(children) == 1:
            return children[0]
        else:
            if lone:
                # if one our children does not have a getChild method we
                # want to hand the request over to it from then on,
                # which should not be done if there are multiple
                # children on this subptah
                raise 'multiple subpath matches vs. asocial child for %s' % subpath
            else:
                return ShadowCollection(children)

    def handle(self, request, reply, subpath):
        if request.path.endswith('/'):
            self.getChild(request, reply, '').handle(request, reply, subpath)
        else:
            reply.headers.setHeader('Location', request.path + '/')
            raise error.web.MovedPermanently


