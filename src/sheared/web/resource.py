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

class Resource:
    method_parsers = None
    def __init__(self):
        if self.method_parsers is None:
            self.method_parsers = {}
    def getMethodParser(self, method):
        return self.method_parsers.get(method, None)

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
            raise error.web.BadRequestError

        ct = request.headers.get('Content-Type')
        if ct == 'application/x-www-form-urlencoded':
            qs = request.body.lstrip()
            request.args = querystring.HTTPQueryString(qs)

        else:
            print 'need handler for POST with Content-Type %r' % ct
            raise error.web.NotImplementedError

class NormalResource(GettableResource, PostableResource):
    def __init__(self):
        GettableResource.__init__(self)
        PostableResource.__init__(self)
