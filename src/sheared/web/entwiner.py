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
import os
import sha

from entwine import entwine

from sheared.python import io
from sheared.web import resource
from sheared import error

class Entwiner(resource.NormalResource):
    def __init__(self):
        resource.NormalResource.__init__(self)

        if hasattr(self, 'template_page'):
            self.template_pages = [self.template_page]
        else:
            self.templates_pages = []

    def handle(self, request, reply, subpath):
        self.context = {}
        if hasattr(request, 'context'):
            self.context.update(request.context)

        self.entwine(request, reply, subpath)
    
        for i in range(len(self.template_pages)):
            last = i == range(len(self.template_pages))
            r = self.execute(self.template_pages[i], throwaway=last)

        reply.headers.setHeader('Content-Length', str(len(r)))

        # Conditional GET support
        if not reply.headers.has_key('ETag') and \
           not reply.headers.has_key('Last-Modified'):
            etag = '"%s"' % sha.sha(r).hexdigest()
            reply.headers.setHeader('ETag', etag)

            if not request.head_only and \
               request.headers.has_key('If-None-Match'):
                if etag == request.headers['If-None-Match']:
                    raise error.web.NotModified

        reply.send(r)

    def execute(self, path, throwaway=1):
        root = getattr(self, 'template_root', '')
        if root:
            path = [root] + path.split('/')
            path = os.sep.join(path)

        r = entwine(io.readfile(path), self.context)

        if throwaway and r.strip():
            warnings.warn('%s: ignored non-macro content' % path)

        return r
