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

def entwined_handler(request, reply, collection, walker):
    if walker.root.endswith(collection.template_ext):
        templates = [walker.root]
        templates.extend(collection.page_templates)
    
        ctx = {}

        for i in range(len(templates)):
            last = i == len(templates) - 1
            r = entwine(io.readfile(templates[i]), ctx)
            if (not last) and r.strip():
                warnings.warn('ignored generated content from %s' % template,
                              UserWarning, stacklevel=2)
        
        reply.headers.setHeader('Content-Type', 'text/html')
        reply.headers.setHeader('Content-Length', len(r))
        reply.send(r)
    
    else:
        return normal_handler(request, reply, collection, walker)

class EntwinedCollection(FilesystemCollection):
    def __init__(self, page_templates, *a, **kw):
        FilesystemCollection.__init__(self, *a, **kw)
        self.page_templates = page_templates
        self.normal_handler = entwined_handler
        self.template_ext = '.html'
