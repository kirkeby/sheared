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
from sheared import reactor
from sheared import error
from sheared.python import path
from sheared.protocol import http

import os, mimetypes, stat, errno

class StaticCollection:
    def __init__(self):
        self.bindings = {}

    def bind(self, root, thing):
        self.bindings[root] = thing

    def getChild(self, request, reply, path):
        if not self.bindings.has_key(path):
            raise error.web.NotFoundError('Resource not found.')
        return self.bindings[path]

    def handle(self, request, reply, path):
        if not getattr(self, 'index', None):
            raise error.web.ForbiddenError
        return self.index.handle(request, reply, path)

class FilesystemCollection:
    def __init__(self, root, mt=None):
        self.root = root
        if mt:
            self.mimetypes = mt
        else:
            self.mimetypes = mimetypes.MimeTypes()

    def handle(self, request, reply, subpath):
        abs_path = path.rooted_path(self.root, subpath)
        type, encoding = self.mimetypes.guess_type(abs_path)
        if not type:
            type = 'application/octet-stream'

        try:
            st = os.stat(abs_path)
            if stat.S_ISDIR(st.st_mode):
                raise error.web.ForbiddenError

            elif stat.S_ISREG(st.st_mode):
                file = reactor.open(abs_path, 'r')
                reply.headers.setHeader('Last-Modified', http.HTTPDateTime(st.st_mtime))
                reply.headers.setHeader('Content-Length', st.st_size)
                reply.headers.setHeader('Content-Type', type)
                if encoding:
                    reply.headers.setHeader('Content-Encoding', encoding)
                reply.sendfile(file)
                reply.done()

            else:
                raise error.web.ForbiddenError

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise error.web.NotFoundError
            else:
                raise error.web.ForbiddenError
