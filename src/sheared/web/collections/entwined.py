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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307
# USA
#

import warnings

from entwine import entwine

from sheared.python import io
from sheared.python import log
from sheared.web.collections.filesystem import *
from sheared.web.entwiner import Entwiner

def entwined_handler(request, reply, collection, walker):
    if walker.root.endswith(collection.template_ext):
        entwiner = collection.entwiner(walker.root)
        entwiner.handle(request, reply, walker.path_info)
    else:
        normal_handler(request, reply, collection, walker)

class EntwinedFile(Entwiner):
    def __init__(self, path):
        self.path = path
    def entwine(self, request, reply, subpath):
        self.execute(self.path)
class EntwinedCollection(FilesystemCollection):
    def __init__(self, entwiner=None, *a, **kw):
        FilesystemCollection.__init__(self, *a, **kw)
        if entwiner is None:
            self.entwiner = EntwinedFile
        else:
            self.entwiner = entwiner
        self.normal_handler = entwined_handler
        self.template_ext = '.html'
