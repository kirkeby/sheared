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
from __future__ import nested_scopes

import os, sys, errno, atexit, signal

from sheared import reactor

def normally(name=None, pidfile=1, logfile=1):
    if name is None:
        name = sys.argv[0]
    if pidfile == 1:
        pidfile = name + '.pid'
    if logfile == 1:
        logfile = name + '.log'
    
    background(chdir=0)
    handle_signals()

    if pidfile:
        writepidfile(pidfile)
    if logfile:
        openstdlog(logfile)

def background(chdir=1, close=1):
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
    if close:
        closeall()

def writepidfile(path):
    f = open(path, 'w')
    f.write('%d\n' % os.getpid())
    f.close()

    def unlink():
        os.unlink(path)
    atexit.register(unlink)

def handle_signals():
    def stop(signum, frame):
        reactor.current.shutdown()
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

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

    sys.stdin = open('/dev/zero', 'r', 0)
    sys.stdout = sys.stderr = open(path, 'a', 0)

    assert sys.stdin.fileno() == 0
    assert sys.stdout.fileno() == 1
    os.dup2(1, 2)

def openstdio(stdin='/dev/zero', stdout='/dev/null', stderr='/dev/null'):
    closerange(range(0, 3))

    sys.stdin = open(stdin, 'r', 0)
    sys.stdout = open(stdout, 'w', 0)
    if stderr == stdout:
        sys.stderr = sys.stdout
        os.dup2(1, 2)
    else:
        sys.stderr = open(stderr, 'w', 0)

    assert sys.stdin.fileno() == 0
    assert sys.stdout.fileno() == 1
    assert sys.stderr.fileno() == 2 or sys.stderr is sys.stdout
