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

import base64

from sheared import error

class HTTPRequest:
    def __init__(self, requestline, headers, body):
        self.requestline = requestline
        self.method = requestline.method
        self.path = requestline.uri[2]
        self.headers = headers
        self.body = body

    def parent(self):
        return self.path[self.path.rfind('/') : ]
    
    def sibling(self, uri):
        return self.parent() + '/' + uri

    def child(self, uri):
        if self.path.endswith('/'):
            return self.path + uri
        else:
            return self.path + '/' + uri

    def authentication(self, require=1):
        login, password = None, None

        if self.headers.has_key('authorization'):
            auth = self.headers['authorization']
            try:
                type, auth = auth.split(' ', 2)

                if type == 'Basic':
                    auth = base64.decodestring(auth)
                    login, password = auth.split(':', 2)
                else:
                    return None, None

            except:
                pass

        if require and login is None:
            raise UnauthorizedException, 'authorization required'
        else:
            return login, password

__all__ = ['HTTPRequest']
