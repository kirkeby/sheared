from __future__ import nested_scopes
import os, sys, errno

def background(chdir=1):
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    if os.fork():
        # exit first parent
        sys.exit(0) 

    if chdir:
        os.chdir("/") 

    # decouple from parent environment
    os.setsid() 
    os.umask(0) 

    # do second fork
    if os.fork():
        # exit second parent
        sys.exit(0) 

    # close all open file-descriptors
    closeall()

def writepidfile(path):
    f = open(path, 'w')
    f.write('%d\n' % os.getpid())
    f.close()

def closerange(r):
    for fd in r:
        try:
            os.close(fd)
        except OSError, (eno, _):
            if not eno == errno.EBADF:
                raise

def closeall(min=0):
    fdmax = os.sysconf('SC_OPEN_MAX')
    closerange(range(min, fdmax))

def openstdlog(path):
    closerange(range(0, 3))

    sys.stdin = open('/dev/zero', 'r')
    sys.stdout = sys.stderr = open(path, 'a')

    assert sys.stdin.fileno() == 0
    assert sys.stdout.fileno() == 1
    os.dup2(1, 2)

def openstdio(stdin='/dev/zero', stdout='/dev/null', stderr='/dev/null'):
    closerange(range(0, 3))

    sys.stdin = open(stdin, 'r')
    sys.stdout = open(stdout, 'w')
    sys.stderr = open(stderr, 'w')

    assert sys.stdin.fileno() == 0
    assert sys.stdout.fileno() == 1
    assert sys.stderr.fileno() == 2
