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

import os, mimetypes, stat, errno

from sheared import reactor
from sheared import error
from sheared.python import path
from sheared.protocol import http
from sheared.web import resource

from entwine import abml

class ShadowCollection(resource.GettableResource):
    def __init__(self):
        resource.GettableResource.__init__(self)

        self.layers = []

    def addLayer(self, layer):
        self.layers.append(layer)

    def getChild(self, request, reply, subpath):
        for layer in self.layers:
            try:
                child = layer.getChild(request, reply, subpath)
            except error.web.NotFoundError:
                continue
            break
        else:
            raise error.web.NotFoundError, subpath
        return child

    def handle(self, request, reply, subpath):
        if request.path.endswith('/'):
            self.getChild(request, reply, '').handle(request, reply, subpath)
        else:
            reply.headers.setHeader('Location', request.path + '/')
            raise error.web.MovedPermanently

class StaticCollection(resource.GettableResource):
    def __init__(self):
        resource.GettableResource.__init__(self)

        self.bindings = {}
        self.index = 'index'

    def bind(self, root, thing):
        self.bindings[root] = thing

    def getChild(self, request, reply, subpath):
        if not subpath:
            subpath = self.index
        if not self.bindings.has_key(subpath):
            raise error.web.NotFoundError
        return self.bindings[subpath]

    def handle(self, request, reply, subpath):
        if request.path.endswith('/'):
            self.getChild(request, reply, '').handle(request, reply, subpath)
        else:
            reply.headers.setHeader('Location', request.path + '/')
            raise error.web.MovedPermanently

class FilesystemCollection(resource.NormalResource):
    def __init__(self, root, path_info='', mt=None):
        resource.NormalResource.__init__(self)

        self.root = root
        self.path_info = path_info
        if mt:
            self.mimetypes = mt
        else:
            self.mimetypes = mimetypes.MimeTypes()

        self.index_files = ['index.html']

    def getChild(self, request, reply, subpath):
        try:
            st = os.stat(self.root)
            if stat.S_ISDIR(st.st_mode):
                if subpath:
                    subpaths = [subpath]
                else:
                    subpaths = self.index_files
                for subpath in subpaths:
                    abs_path = self.root + os.sep + subpath
                    if os.access(abs_path, os.F_OK):
                        return FilesystemCollection(abs_path, self.path_info, self.mimetypes)
                return None
            elif stat.S_ISREG(st.st_mode):
                path_info = self.path_info + '/' + subpath
                return FilesystemCollection(self.root, path_info, self.mimetypes)
            else:
                raise error.web.ForbiddenError, 'not a file or directory'

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise error.web.NotFoundError, 'ENOENT'
            else:
                raise error.web.ForbiddenError, 'other OSError'

    def handle(self, request, reply, subpath):
        assert not subpath

        try:
            st = os.stat(self.root)
            if stat.S_ISDIR(st.st_mode):
                if request.path.endswith('/'):
                    index = self.getChild(request, reply, '')
                    if index:
                        index.handle(request, reply, subpath)
                    else:
                        if os.access(self.root, os.X_OK):
                            self.handle_index(request, reply, subpath)
                        else:
                            raise error.web.ForbiddenError, 'directory not listable'
                else:
                    reply.headers.setHeader('Location', request.path + '/')
                    raise error.web.MovedPermanently
            elif stat.S_ISREG(st.st_mode):
                if os.access(self.root, os.X_OK):
                    self.handle_exec(request, reply, subpath)
                elif os.access(self.root, os.R_OK):
                    self.stat = st
                    self.handle_normal(request, reply, subpath)
                else:
                    raise error.web.ForbiddenError, 'not X or R'
            else:
                raise error.web.ForbiddenError, 'not a file or directory'

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise error.web.NotFoundError, 'ENOENT'
            else:
                raise error.web.ForbiddenError, 'other OSError'

    def handle_normal(self, request, reply, subpath):
        type, encoding = self.mimetypes.guess_type(self.root)
        if not type:
            type = 'application/octet-stream'

        last_modified = http.HTTPDateTime(self.stat.st_mtime)

        reply.headers.setHeader('Last-Modified', last_modified)
        reply.headers.setHeader('Content-Length', self.stat.st_size)
        reply.headers.setHeader('Content-Type', type)
        if encoding:
            reply.headers.setHeader('Content-Encoding', encoding)

        file = reactor.open(self.root, 'r')
        reply.sendfile(file)
        reply.done()

    def handle_exec(self, request, reply, subpath):
        raise error.web.ForbiddenError, 'cgi-scripts not allowed: %s' % self.root

    def handle_index(self, request, reply, subpath):
        reply.transport.write('<html>\r\n'
                    '<head><title>Some directory index</title></head>\r\n'
                    '<body>\r\n')
        for file in os.listdir(self.root):
            reply.transport.write('<a href="%s">%s</a><br />\r\n' % (
                file.replace('"', '\\"'),
                abml.quote(file),
            ))
        reply.transport.write('</body></html>\r\n')
        reply.transport.close()
