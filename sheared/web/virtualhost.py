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

        pieces = path.canonical_path(pth.split('/'))
        while pieces:
            if getattr(child, 'authenticate', None):
                child.authenticate(request, reply)
            if not getattr(child, 'isLeaf', getattr(child, 'getChild', None)):
                break
            piece = pieces.pop(0)
            child = child.getChild(request, reply, piece)
        
        return child, '/'.join(pieces)

    def handle(self, request, reply, path):
        child, subpath = self.walkPath(request, reply, path)

        if not getattr(child, 'handle', None):
            raise error.web.ForbiddenError

        child.handle(request, reply, subpath)

