#!/usr/bin/env python
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

import os, sys, socket, time
from sheared.python import fdpass

pid = os.fork()
if pid:
    # Open a file for passing along to child. Use own source code,
    # which is guaranteed to exist. :)
    fd = os.open(sys.argv[3], os.O_RDONLY)
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        os.unlink(sys.argv[1])
    except:
        pass
    sock.bind(sys.argv[1])
    sock.listen(5)
    conn, cli = sock.accept()

    fdpass.send(conn.fileno(), fd, sys.argv[3])
    conn.close()

    # Wait for child to terminate, then exit.
    os.waitpid(pid, 0)
    sys.exit(0)

else:
    time.sleep(1)

    # Receive filedescriptor. Will block until descriptor is sent.
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
#    try:
#        os.unlink(sys.argv[2])
#    except:
#        pass
#    sock.bind(sys.argv[2])
    sock.connect(sys.argv[1])

    fd, path = fdpass.recv(sock.fileno())

    # Example usage: Read file, print the first line.
    fileObj = os.fdopen(fd, 'r')
    lines = fileObj.readlines()
    print lines[0],
    sys.exit(0)


