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

import time

class CombinedLog:
    def __init__(self, log):
        self.log = log

    def logRequest(self, request, reply):
        ip, port = reply.transport.other
        ident = '-'
        auth = request.authentication()
        if auth:
            user = auth[1]
        else:
            user = '-'
        date = time.strftime('%d/%m/%Y:%H:%M:%S %z')
        req = request.requestline.raw
        code = reply.status
        length = 0

        if request.headers.has_key('Referer'):
            referer = request.headers.get('Referer')
        else:
            referer = ''

        if request.headers.has_key('User-Agent'):
            agent = request.headers.get('User-Agent')
        else:
            agent = ''

        fmt = '%s %s %s [%s] "%s" %d %d "%s" "%s"\n'
        self.log.write(fmt % (ip, ident, user, date,
                              req, code, length,
                              referer, agent))
