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
from sheared.web import querystring
from sheared.python.rfc1521 import parse_plist_header
from sheared.python.rfc1521 import parse_content_type

class Resource:
    method_parsers = None
    def __init__(self):
        if self.method_parsers is None:
            self.method_parsers = {}
    def getMethodParser(self, method):
        return self.method_parsers.get(method, None)

    def handle(self, request, reply, subpath):
        raise NotImplementedError
    def authenticate(self, request, reply):
        pass

class GettableResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.method_parsers['GET'] = self.parseGet
        self.method_parsers['HEAD'] = self.parseHead

    def parseGet(self, request, reply):
        if request.body:
            raise error.web.BadRequestError
        qs = request.requestline.uri[3]
        request.args = querystring.HTTPQueryString(qs)

    def parseHead(self, request, reply):
        self.parseGet(request, reply)
        request.head_only = reply.head_only = 1

class PostableResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.method_parsers['POST'] = self.parsePost

    def parsePost(self, request, reply):
        if not request.headers.has_key('Content-Type'):
            raise error.web.BadRequestError, \
                  "can't POST without a Content-Type"

        ct, params = parse_content_type(request.headers.get('Content-Type'))
        if ct == 'application/x-www-form-urlencoded':
            qs = request.body.lstrip()
            request.args = querystring.HTTPQueryString(qs)

        elif ct == 'multipart/form-data':
            parts = request.body.split('--' + params['boundary'])
            if len(parts) < 2:
                raise ValueError, 'what kind of degenerate madness is this?!'
            if not parts[-1][:2] == '--':
                raise ValueError, 'bad end-boundary'
            parts = map(RFC822Message, parts[1:-1])

            args = {}
            for part in parts:
                # FIXME -- handle encodings and other funkiness
                cd = part.headers['Content-Disposition'][0]
                disp, params = parse_plist_header(cd)
                val = querystring.UnvalidatedInput(params['name'], part.body)
                args[params['name']] = [val]
            request.args = querystring.Form(args)

        else:
            raise error.web.NotImplementedError, \
                  'need handler for POST with Content-Type %r' % ct

class NormalResource(GettableResource, PostableResource):
    def __init__(self):
        GettableResource.__init__(self)
        PostableResource.__init__(self)

class MovedResource(NormalResource):
    def __init__(self, dst):
        NormalResource.__init__(self)
        self.destination = dst

    def getChild(self, request, reply, subpath):
        return MovedResource(self.destination + '/' + subpath)
    
    def handle(self, request, reply, subpath):
        assert not subpath
        reply.headers.setHeader('Location', self.destination)
        raise error.web.MovedPermanently

class AliasedResource:
    def __init__(self, resource, location):
        self.resource = resource
        self.location = location

    def getMethodParser(self, method):
        return self.resource.getMethodParser(method)

    def handle(self, request, reply, subpath):
        assert not subpath
        reply.headers.setHeader('Location', self.location)
        self.resource.handle(request, reply, subpath)
