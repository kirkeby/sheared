import os, sys, errno

def daemonize():
    # do the UNIX double-fork magic, see Stevens' "Advanced 
    # Programming in the UNIX Environment" for details (ISBN 0201563177)
    if os.fork():
        # exit first parent
        sys.exit(0) 

    # decouple from parent environment
    os.chdir("/") 
    os.setsid() 
    os.umask(0) 

    # do second fork
    if os.fork():
        # exit second parent
        sys.exit(0) 

    # close all open file-descriptors
    fdmax = os.sysconf('SC_OPEN_MAX')
    for fd in range(fdmax):
        try:
            os.close(fd)
        except OSError, (eno, _):
            if not eno == errno.EBADF:
                raise
