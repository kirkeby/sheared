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
        if reactor.current.started:
            stdin = reactor.current.prepareFile(stdin_w)
            stdout = reactor.current.prepareFile(stdout_r)
        else:
            stdin = stdin_w
            stdout = stdout_r
        stderr = reactor.current.prepareFile(stderr_r)

    else:
        try:
            os.dup2(stdin_r, 0)
            os.dup2(stdout_w, 1)
            os.dup2(stderr_w, 2)
            daemonize.closeall(3)
            os.execv(cmd, argv)
        except:
            # sys.exit raises SystemExit which is caught by
            # try/excepts deep in the bowels of the reactor
            # core. So we do this instead:
            os.execv("/bin/false", ["/bin/false"])
        
    if with_stderr:
        return pid, stdin, stdout, stderr
    else:
        return pid, stdin, stdout

def getstatusoutput(cmd, argv):
    pid, stdin, stdout = spawn(cmd, argv)
    if reactor.current.started:
        reactor.current.close(stdin)
    else:
        os.close(stdin)
    
    out = ''
    while 1:
        if reactor.current.started:
            d = reactor.current.read(stdout, 4096)
        else:
            d = os.read(stdout, 4096)
        if d == '':
            break
        out = out + d

    # FIXME -- just because a process closes stdout does not mean
    # it is done
    status = os.waitpid(pid, os.WNOHANG)
    return status[1], out

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


