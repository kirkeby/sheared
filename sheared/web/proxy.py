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
from sheared import reactor

class DumbProxy:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def handle(self, request, reply):
        try:
            version = request.requestline.version[0]
            transport = reactor.connectTCP((self.host, self.port))
            
            transport.write('%s\r\n' % request.requestline.raw)
            if version == 1:
                for k, v in request.headers.items():
                    transport.write('%s: %s\r\n' % (k, v))
                transport.write('\r\n')
                transport.write(request.body)

            reply.transport.sendfile(transport)

        except OSError:
            pass

        transport.close()
