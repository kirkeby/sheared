#!/usr/bin/env python

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


