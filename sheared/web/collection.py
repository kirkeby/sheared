from sheared import reactor
from sheared import error
from sheared.protocol import http

import os, mimetypes, stat, errno

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

    def handle(self, request, reply, subpath):
        path = [self.root]
        for piece in subpath.split('/'):
            if piece == '..':
                if len(path) > 1:
                    path.pop()
            elif piece == '.' or piece == '':
                pass
            else:
                path.append(piece)

        path = os.sep.join(path)
        type, encoding = mimetypes.guess_type(path)
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
