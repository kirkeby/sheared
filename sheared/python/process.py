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
import os, pickle, sys

from sheared import reactor
from sheared.python import io

def runInChildProcess(f, args=(), kwargs={}):
    r, w = os.pipe()

    pid = os.fork()
    if pid:
        os.close(w)
        rv = io.readall(reactor.openfd(r, '<%r pipe>' % f))
        while not os.waitpid(pid, os.WNOHANG)[0] == pid:
            reactor.sleep(1)

        rv, exc = pickle.loads(rv)
        if exc:
            raise exc
        else:
            return rv

    else:
        try:
            v = apply(f, args, kwargs), None
        except:
            v = None, sys.exc_info()[1]
        os.write(w, pickle.dumps(v))

        # sys.exit raises SystemExit which is caught by try/excepts deep
        # in the bowels of the reactor core. So we do this instead:
        os.execv("/bin/true", ["/bin/true"])
