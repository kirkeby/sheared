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

from sheared import error
from sheared.python import path

class VirtualHost:
    def __init__(self, collection):
        self.collection = collection

    def walkPath(self, request, reply, pth):
        child = self.collection

        authenticated = 1
        pieces = path.canonical_path(pth.split('/'))
        while pieces:
            if getattr(child, 'authenticate', None):
                child.authenticate(request, reply)
            authenticated = 1
            if not getattr(child, 'getChild', None):
                break
            piece = pieces.pop(0)
            child = child.getChild(request, reply, piece)
            authenticated = 0
        
        if not authenticated and getattr(child, 'authenticate', None):
            child.authenticate(request, reply)
        return child, '/'.join(pieces)

    def handle(self, request, reply):
        if request.requestline.uri[0] or request.requestline.uri[1]:
            raise error.web.ForbiddenError

        path = request.requestline.uri[2]

        try:
            child, subpath = self.walkPath(request, reply, path)

            if child is None:
                raise error.web.NotFoundError, path
            if not getattr(child, 'handle', None):
                raise error.web.ForbiddenError, `child`

            mp = child.getMethodParser(request.requestline.method)
            if not mp:
                raise error.web.NotImplementedError
            mp(request, reply)
            
            child.handle(request, reply, subpath)

        except error.web.Moved, e:
            self.massageLocationHeader(request, reply)
            raise

    def massageLocationHeader(self, request, reply):
        if not reply.headers.has_key('Location'):
            raise error.web.InternalServerError

        loc = reply.headers.get('Location')
        if loc.find('://') < 0 and request.headers.has_key('Host'):
            if not loc.startswith('/'):
                loc = request.path + '/' + loc
            loc = 'http://' + request.headers['Host'] + loc
            reply.headers.setHeader('Location', loc)
