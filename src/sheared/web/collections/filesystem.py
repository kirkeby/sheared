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
from sheared.python import io
from sheared.protocol import http
from sheared.web import resource

import abml

def htaccess_authenticator(request, reply, collection, walker):
    htaccess = walker.root + os.sep + '.htaccess'
    if os.access(htaccess, os.R_OK):
        authname = ''
        htpasswd = ''
        require = ''

        f = io.BufferedReader(reactor.open(htaccess, 'r'))
        for line in f.readlines():
            op, arg = line.strip().split(' ', 1)
            if op == 'AuthName':
                authname = arg
            elif op == 'AuthUserFile':
                htpasswd = arg
            elif op == 'require':
                require = arg
        
        if authname:
            good = 0
            auth = request.authentication()
            if auth:
                scheme, login, password = auth
                
                if scheme == 'Basic':
                    f = io.BufferedReader(reactor.open(htpasswd, 'r'))
                    for line in f.readlines():
                        u, p = line.strip().split(':', 1)
                        if u == login and p == password:
                            good = 1
                            break

            if not good:
                hdr = 'Basic realm=%s' % authname
                reply.headers.setHeader('WWW-Authenticate', hdr)
                raise error.web.UnauthorizedError

def normal_handler(request, reply, collection, walker):
    type, encoding = collection.mimetypes.guess_type(walker.root)
    if not type:
        type = 'application/octet-stream'

    last_modified = http.HTTPDateTime(walker.stat.st_mtime)

    reply.headers.setHeader('Last-Modified', str(last_modified))
    reply.headers.setHeader('Content-Length', str(walker.stat.st_size))
    reply.headers.setHeader('Content-Type', str(type))
    if encoding:
        reply.headers.setHeader('Content-Encoding', str(encoding))

    # Conditional GET support
    if not request.head_only and request.headers.has_key('If-Modified-Since'):
        try:
            when = http.HTTPDateTime(request.headers['If-Modified-Since'])
        except ValueError:
            pass
        else:
            if not last_modified.unixtime > when.unixtime:
                raise error.web.NotModified

    file = reactor.open(walker.root, 'r')
    reply.sendfile(file)
    reply.done()

def index_handler(request, reply, collection, walker):
    reply.headers.setHeader('Content-Type', 'text/html')
    reply.send('<html>\r\n'
                '<head><title>Some directory index</title></head>\r\n'
                '<body>\r\n')
    for file in os.listdir(walker.root):
        reply.send('<a href="%s">%s</a><br />\r\n' % (
            file.replace('"', '\\"'),
            abml.abmlify(file),
        ))
    reply.send('</body></html>\r\n')
    reply.done()

def forbidden_handler(request, reply, collection, walker):
    raise error.web.ForbiddenError

class FilesystemCollection(resource.NormalResource):
    def __init__(self, root, allow_indexing=0):
        resource.NormalResource.__init__(self)

        self.walker = FilesystemWalker(self, root, '')
        self.mimetypes = mimetypes.MimeTypes()

        self.index_files = ['index.html']

        self.authenticator = htaccess_authenticator
        self.normal_handler = normal_handler
        self.index_handler = forbidden_handler
        self.exec_handler = forbidden_handler
        
        if allow_indexing:
            self.index_handler = index_handler

    def authenticate(self, request, reply):
        return self.walker.authenticate(request, reply)
    def handle(self, request, reply, subpath):
        return self.walker.handle(request, reply, subpath)
    def getChild(self, request, reply, subpath):
        return self.walker.getChild(request, reply, subpath)

    def handle_normal(self, request, reply, walker):
        if self.normal_handler:
            self.normal_handler(request, reply, self, walker)
        else:
            raise error.web.ForbiddenError, 'No handler for this type ' \
                                            'of resource %s' % self.root
    def handle_exec(self, request, reply, walker):
        if self.exec_handler:
            self.exec_handler(request, reply, self, walker)
        else:
            raise error.web.ForbiddenError, 'No handler for this type ' \
                                            'of resource %s' % self.root
    def handle_index(self, request, reply, walker):
        if self.index_handler:
            self.index_handler(request, reply, self, walker)
        else:
            raise error.web.ForbiddenError, 'No handler for this type ' \
                                            'of resource %s' % self.root


class FilesystemWalker(resource.NormalResource):
    def __init__(self, collection, root, path_info):
        resource.NormalResource.__init__(self)

        self.collection = collection

        self.root = root
        self.path_info = path_info

    def authenticate(self, request, reply):
        if self.collection.authenticator:
            self.collection.authenticator(request, reply, self.collection, self)
        
    def getChild(self, request, reply, subpath):
        try:
            st = os.stat(self.root)
            if stat.S_ISDIR(st.st_mode):
                if subpath:
                    subpaths = [subpath]
                else:
                    subpaths = self.collection.index_files
                for subpath in subpaths:
                    abs_path = self.root + os.sep + subpath
                    if os.access(abs_path, os.F_OK):
                        return self.createChild(abs_path, self.path_info)
                raise error.web.NotFoundError
            elif stat.S_ISREG(st.st_mode):
                path_info = self.path_info + '/' + subpath
                return self.createChild(self.root, path_info)
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
                    try:
                        index = self.getChild(request, reply, '')
                        index.handle(request, reply, subpath)
                    except error.web.NotFoundError:
                        if os.access(self.root, os.X_OK):
                            self.collection.handle_index(request, reply, self)
                        else:
                            raise error.web.ForbiddenError, 'directory not listable'
                else:
                    reply.headers.setHeader('Location', request.path + '/')
                    raise error.web.MovedPermanently
            elif stat.S_ISREG(st.st_mode):
                if os.access(self.root, os.X_OK):
                    self.collection.handle_exec(request, reply, self)
                elif os.access(self.root, os.R_OK):
                    self.stat = st
                    self.collection.handle_normal(request, reply, self)
                else:
                    raise error.web.ForbiddenError, 'not X or R'
            else:
                raise error.web.ForbiddenError, 'not a file or directory'

        except OSError, ex:
            if ex.errno == errno.ENOENT:
                raise error.web.NotFoundError, 'ENOENT'
            else:
                raise error.web.ForbiddenError, 'other OSError'

    def createChild(self, root, path_info):
        return self.__class__(self.collection, root, path_info)

__all__ = ['FilesystemCollection', 'htaccess_authenticator',
           'normal_handler', 'index_handler']
