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
import os
import sys
import sha
import warnings
import traceback
import encodings

from entwine import entwine

from sheared.python import io
from sheared.web import accept
from sheared.web import resource
from sheared import error

class TemplateError(Exception):
    pass

class Entwiner(resource.NormalResource):
    macro_pages = []
    template_pages = []
    content_types = [
        'application/xhtml+xml',
        'text/html',
        'text/xml',
    ]
    charset = 'utf8'
    
    def __init__(self):
        resource.NormalResource.__init__(self)

    def handle(self, request, reply, subpath):
        # Reset state
        self.result = None

        # Accept support
        ct = accept.chooseContentType(request, self.content_types)
        ct = ct + '; charset=%s' % self.charset
        reply.headers.setHeader('Content-Type', ct)
        reply.headers.addHeader('Vary', 'Accept')
    
        self.context = {}
        if hasattr(request, 'context'):
            self.context.update(request.context)

        for template in self.macro_pages:
            self.execute(template)
        self.entwine(request, reply, subpath)
        for template in self.template_pages:
            self.execute(template)
        if self.result is None:
            raise TemplateError, 'no result'
    
        reply.headers.setHeader('Content-Length', str(len(self.result)))

        # Conditional GET support
        if not reply.headers.has_key('ETag') and \
           not reply.headers.has_key('Last-Modified'):
            etag = '"%s"' % sha.sha(self.result).hexdigest()
            reply.headers.setHeader('ETag', etag)

            if not request.head_only and \
               request.headers.has_key('If-None-Match'):
                if etag == request.headers['If-None-Match']:
                    raise error.web.NotModified

        reply.send(self.result)

    def execute(self, path):
        root = getattr(self, 'template_root', '')
        if root:
            path = [root] + path.split('/')
            path = os.sep.join(path)

        result = entwine(io.readfile(path), self.context, source=path)
        if result.strip():
            if not self.result is None:
                warnings.warn('%s: multiple results' % path)
            encoder = encodings.search_function(self.charset)[0]
            self.result = encoder(result)[0]
