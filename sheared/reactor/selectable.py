# vim:nowrap:textwidth=0
import select, sys, types, fcntl, os, socket, traceback, errno

from sheared.python import coroutine
from sheared.internet import tcp
from sheared.reactor import transport

# FIXME -- this would be so much nicer if we had a Reactor class

reactor = sys.modules['sheared.reactor.selectable']

def do_shutdown(co, r):
    global result
    result = r

def do_sleep(co, n):
    until = now + n
    for i in range(len(sleeping)):
        if sleeping[i][0] >= until:
            sleeping.insert(i, (until, co))
    else:
        sleeping.append((until, co))
    
def do_add(oco, nco, args):
    coroutines.append((nco, args))
    coroutines.append((oco, ()))

def do_done(co):
    co()

def do_accept(co, fd):
    accepting[fd] = co

def do_connect(co, fd, addr):
    connecting[fd] = co
    try:
        fd.connect(addr)
    except socket.error, e:
        if e[0] == errno.EINPROGRESS:
            pass
        else:
            raise

def do_read(co, fd, n):
    if not isinstance(fd, types.IntType):
        fd = fd.fileno()
    reading[fd] = co, n

def do_write(co, fd, d):
    if not isinstance(fd, types.IntType):
        fd = fd.fileno()
    writing[fd] = co, d

def call(co, *args):
    try:
        op, args = apply(co, args)
        apply(op, (run.caller,) + args)
    except coroutine.CoroutineFailed, ex:
        print 'CoroutineFailed:', co.name
        apply(traceback.print_exception, ex[0].exc_info)
    except coroutine.CoroutineReturned:
        pass

def mainloop():
    global running
    running = 1

    try:
        while not hasattr(reactor, 'result'):
            global now
            # this is icky, but unix is poorly lacking in anything resembling a global clock
            now = float(file('/proc/uptime').readline().split()[0])

            while coroutines:
                co, args = coroutines.pop(0)
                apply(call, (co,) + args)

            read = {}
            read.update(reading)
            read.update(accepting)
            read = read.keys()
            write = {}
            write.update(writing)
            write.update(connecting)
            write = write.keys()
            both = {}
            both.update(reading)
            both.update(writing)
            both = both.keys()
    
            if not read and not write and not sleeping:
                return

            if sleeping:
                timeout = sleeping[0][0] - now
                if timeout >= 0:
                    readable, writable, errable = select.select(read, write, both, timeout)
                else:
                    readable, writable, errable = (), (), ()
            else:
                readable, writable, errable = select.select(read, write, both)

            while sleeping and sleeping[0][0] <= now:
                _, co = sleeping.pop(0)
                apply(call, (co, ()))

            for fd in errable:
                raise NotImplementedError, 'error-handling not yet implemented'

            for fd in readable:
                if reading.has_key(fd):
                    co, n = reading[fd]
                    del reading[fd]
                
                    data = os.read(fd, n)
                    call(co, data)

                elif accepting.has_key(fd):
                    co = accepting[fd]
                    del accepting[fd]

                    data = fd.accept()
                    call(co, data)

                else:
                    raise 'this cannot happen'

            for fd in writable:
                if writing.has_key(fd):
                    co, d = writing[fd]
                    n = os.write(fd, d)
                    if n == len(d):
                        del writing[fd]
                        call(co, d)
                    
                    else:
                        writing[fd] = co, d[n:]

                elif connecting.has_key(fd):
                    co = connecting[fd]
                    del connecting[fd]

                    err = fd.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    call(co, err)

    finally:
        running = 0

running = 0
def reset():
    assert not running

    global run, coroutines, accepting, reading, writing, sleeping, connecting
    run = coroutine.Coroutine(mainloop)
    coroutines = []
    accepting = {}
    reading = {}
    writing = {}
    sleeping = []
    connecting = {}

    if reactor.__dict__.has_key('result'):
        del reactor.__dict__['result']
reset()

def sleep(n):
    return run(do_sleep, (n,))

def read(fd, n):
    return run(do_read, (fd, n))

def write(fd, d):
    run(do_write, (fd, d))

def accept(fd):
    return run(do_accept, (fd,))

def connect(fd, addr):
    err = run(do_connect, (fd, addr))
    if err:
        raise socket.error, (err, os.strerror(err))

def shutdown(r):
    run(do_shutdown, (r,))


def prepareFile(fd):
    if not isinstance(fd, types.IntType):
        fd = fd.fileno()
    fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK)

def addCoroutine(coroutine, args):
    if running:
        run(do_add, (coroutine, args))
    else:
        coroutines.append((coroutine, args))

def listenTCP(factory, address):
    port = tcp.Port(reactor, factory, address)
    port.listen()

def createTransport(fd, addr):
    return transport.ReactorTransport(reactor, fd, addr)

__all__ = ['run', 'reset', 'read', 'write', 'accept',
           'prepareFile', 'addCoroutine', 'listenTCP']
