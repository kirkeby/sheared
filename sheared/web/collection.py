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
from sheared.protocol import http

import os, mimetypes, stat, errno

def rooted_path(root, subpath):
    path = [root]
    for piece in subpath.split('/'):
        if piece == '..':
            if len(path) > 1:
                path.pop()
        elif piece == '.' or piece == '':
            pass
        else:
            path.append(piece)

    return os.sep.join(path)

class StaticCollection:
    isWalkable = 1

    def __init__(self):
        self.bindings = {}

    def getChild(self, path):
        if not path:
            path = 'index'
        if not self.bindings.has_key(path):
            raise error.web.NotFoundError('Resource not found.')
        return self.bindings[path]

    def bind(self, root, thing):
        self.bindings[root] = thing

class FilesystemCollection:
    isWalkable = 0

    def __init__(self, root):
        self.root = root
        self.mimetypes = mimetypes.MimeTypes()

    def handle(self, request, reply, subpath):
        path = rooted_path(self.root, subpath)
        type, encoding = self.mimetypes.guess_type(path)
        if not type:
            type = 'application/octet-stream'

        try:
            st = os.stat(path)
            if stat.S_ISDIR(st.st_mode):
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'Indexing forbidden.')

            elif stat.S_ISREG(st.st_mode):
                file = open(path, 'r')
                file = reactor.current.prepareFile(file)
                reply.headers.setHeader('Last-Modified', http.HTTPDateTime(st.st_mtime))
                reply.headers.setHeader('Content-Length', st.st_size)
                reply.headers.setHeader('Content-Type', type)
                if encoding:
                    reply.headers.setHeader('Content-Encoding', encoding)
                reply.sendfile(file)
                reply.done()

            else:
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'You may not view this resource.')

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                reply.sendErrorPage(http.HTTP_NOT_FOUND, 'No such file or directory.')
            else:
                reply.sendErrorPage(http.HTTP_FORBIDDEN, 'You may not view this resource.')
