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
import os

from sheared import reactor
from sheared.python import daemonize

def spawn(cmd, argv, with_stderr=0):
    stdin_r, stdin_w = os.pipe()
    stdout_r, stdout_w = os.pipe()
    if with_stderr:
        stderr_r, stderr_w = os.pipe()
    else:
        stderr_r, stderr_w = stdout_r, stdout_w

    pid = os.fork()
    if pid:
        os.close(stdin_r)
        os.close(stdout_w)
        if with_stderr:
            os.close(stderr_w)

        stdin = reactor.fdopen(stdin_w, '<%r stdin>' % cmd)
        stdout = reactor.fdopen(stdout_r, '<%r stdout>' % cmd)
        if with_stderr:
            stderr = reactor.fdopen(stderr_r, '<%r stderr>' % cmd)

    else:
        try:
            os.dup2(stdin_r, 0)
            os.dup2(stdout_w, 1)
            os.dup2(stderr_w, 2)
            daemonize.closeall(3)
            os.execv(cmd, argv)
        except:
            os._exit(1)
        
    if with_stderr:
        return pid, stdin, stdout, stderr
    else:
        return pid, stdin, stdout

def getstatusoutput(cmd, argv):
    pid, stdin, stdout = spawn(cmd, argv)
    
    out = ''
    while 1:
        d = stdout.read()
        if d == '':
            break
        out = out + d

    return waitpid(pid)[1], out

def waitpid(pid, interval=0):
    while 1:
        status = os.waitpid(pid, os.WNOHANG)
        if status[0]:
            break
        if interval:
            reactor.sleep(interval)
    assert status[0] == pid, '%d is not %d' % (status[0], pid)
    return status

def getoutput(cmd, argv):
    return getstatusoutput(cmd, argv)[1]

def isok(status):
    if os.WIFEXITED(status):
        if os.WEXITSTATUS(status):
            return 0
        else:
            return 1
    else:
        return 0


