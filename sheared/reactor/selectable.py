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

#def do_open(co, path, mode):
#    flags = os.O_NONBLOCK
#    if mode == 'r':
#        flags = flags | os.O_RDONLY
#    elif mode == 'w':
#        flags = flags | os.O_RDWR
#    else:
#        co.sendException(ValueError, 'bad flags')
#    connecting = 
#    os.open(path, flags)

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
        apply(op, (main_co.caller,) + args)
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

            # FIXME -- if we are passed a bad file-descriptor (a closed one for instance) select.select
            # will bonk out. so we should do clean-up in that case.
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

    global main_co, coroutines, accepting, reading, writing, sleeping, connecting
    main_co = coroutine.Coroutine(mainloop, 'selectable reactor mainloop')
    coroutines = []
    accepting = {}
    reading = {}
    writing = {}
    sleeping = []
    connecting = {}

    if reactor.__dict__.has_key('result'):
        del reactor.__dict__['result']
reset()

def run():
    try:
        main_co()
    except coroutine.CoroutineReturned:
        pass
    except coroutine.CoroutineFailed, e:
        exc_info = e.args[0].exc_info
        raise exc_info[0], exc_info[1], exc_info[2]

def sleep(n):
    return main_co(do_sleep, (n,))

#def open(fd, n):
#    return main_co(do_open, (path,))

def getfd(file):
    if isinstance(file, types.IntType):
        return file
    else:
        return file.fileno()

def read(fd, n):
    return main_co(do_read, (getfd(fd), n))

def write(fd, d):
    main_co(do_write, (getfd(fd), d))

def accept(fd):
    return main_co(do_accept, (fd,))

def connect(fd, addr):
    err = main_co(do_connect, (fd, addr))
    if err:
        raise socket.error, (err, os.strerror(err))

def close(fd):
    return os.close(getfd(fd))

def shutdown(r):
    main_co(do_shutdown, (r,))

def prepareFile(file):
    fcntl.fcntl(getfd(file), fcntl.F_SETFL, os.O_NONBLOCK)
    return file

def addCoroutine(coroutine, args):
    if running:
        main_co(do_add, (coroutine, args))
    else:
        coroutines.append((coroutine, args))

def connectTCP(factory, address, *args, **kwargs):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    reactor.prepareFile(sock)
    reactor.connect(sock, address)
    transport = createTransport(sock, address)
    return apply(factory, (reactor, transport) + args, kwargs)

def listenTCP(factory, address):
    port = tcp.TCPPort(reactor, factory, address)
    port.listen()

def createTransport(fd, addr):
    return transport.ReactorTransport(reactor, fd, addr)

__all__ = ['run', 'reset', 'read', 'write', 'accept',
           'prepareFile', 'addCoroutine', 'listenTCP', 'connectTCP']
