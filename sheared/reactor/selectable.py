# vim:nowrap:textwidth=0
import select, socket, sys, types, fcntl, os, traceback, errno

from sheared.python import coroutine
from sheared.internet import shocket
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

def do_open(co, path, mode):
    flags = os.O_NONBLOCK
    if mode == 'r':
        flags = flags | os.O_RDONLY
    elif mode == 'w':
        flags = flags | os.O_RDWR
    else:
        co.sendException(ValueError, 'bad flags')
    os.open(path, flags)

def do_accept(co, fd, sock):
    accepting[fd] = co, sock

def do_connect(co, fd, sock, addr):
    connecting[fd] = co, sock
    try:
        sock.connect(addr)
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

            readable, writable, errable = (), (), ()
            try:
                if sleeping:
                    timeout = sleeping[0][0] - now
                    if timeout >= 0:
                        readable, writable, errable = select.select(read, write, both, timeout)
                else:
                    readable, writable, errable = select.select(read, write, both)

            except select.error, (eno, emsg):
                for fd in reading.keys():
                    try:
                        select.select([fd], [], [], 0)
                    except select.error:
                        print 'reading from %r failed' % fd
                        call(reading[fd][0], IOError, (eno, emsg))
                        del reading[fd]
                for fd in accepting.keys():
                    try:
                        select.select([fd], [], [], 0)
                    except select.error:
                        print 'accepting from %r failed' % fd
                        call(accepting[fd][0], IOError, (eno, emsg))
                        del accepting[fd]
                for fd in writing.keys():
                    try:
                        select.select([fd], [], [], 0)
                    except select.error, err:
                        print 'writing to %r failed' % fd
                        call(writing[fd][0], IOError, (eno, emsg))
                        del writing[fd]
                        
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
                    co, sock = accepting[fd]
                    del accepting[fd]

                    data = sock.accept()
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
                    co, sock = connecting[fd]
                    del connecting[fd]

                    err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
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

def call_main(*args, **kwargs):
    rv = apply(main_co, args, kwargs)
    if isinstance(rv, types.TupleType) and len(rv) > 0 and \
       isinstance(rv[0], types.ClassType) and issubclass(rv[0], Exception):
        raise rv[0]
    return rv

def sleep(n):
    return call_main(do_sleep, (n,))

def open(path):
    return call_main(do_open, (path,))

def getfd(file):
    if isinstance(file, types.IntType):
        return file
    else:
        return file.fileno()

def read(fd, n):
    return call_main(do_read, (getfd(fd), n))

def write(fd, d):
    call_main(do_write, (getfd(fd), d))

def accept(fd):
    return call_main(do_accept, (getfd(fd), fd))

def connect(fd, addr):
    err = call_main(do_connect, (getfd(fd), fd, addr))
    if err:
        raise socket.error, (err, os.strerror(err))

def bind(fd, addr):
    return fd.bind(addr)

def listen(fd, backlog):
    return fd.listen(backlog)

def close(fd):
    if isinstance(fd, types.IntType):
        return os.close(fd)
    else:
        return fd.close()

def shutdown(r):
    call_main(do_shutdown, (r,))

def prepareFile(file):
    fcntl.fcntl(getfd(file), fcntl.F_SETFL, os.O_NONBLOCK)
    return file

def addCoroutine(coroutine, args):
    if running:
        call_main(do_add, (coroutine, args))
    else:
        coroutines.append((coroutine, args))

def connectSocket(factory, address, from_addr, klass):
    try:
        client = klass(reactor, address, from_addr)
        transport = client.connect()
        coroutine = self.factory.buildCoroutine(transport)
        self.reactor.addCoroutine(self.coroutine, (None,))
    except socket.error:
        self.reactor.addCoroutine(self.coroutine, (sys.exc_info(),))

def connectTCP(address):
    return connectSocket(factory, address, None, shocket.TCPClient)

def connectUNIX(factory, address):
    return connectSocket(factory, address, None, shocket.UNIXClient)
    
def listenTCP(factory, address):
    port = shocket.TCPPort(reactor, factory, address)
    port.listen()
    return port

def listenUNIX(factory, address):
    port = shocket.UNIXPort(reactor, factory, address)
    port.listen()
    return port

def createTransport(fd, addr):
    return transport.ReactorTransport(reactor, fd, addr)

__all__ = ['run', 'reset', 'read', 'write', 'accept', 'connect', 'bind', 'listen', 'close',
           'prepareFile', 'addCoroutine', 'listenTCP', 'connectTCP', 'createTransport',
           'listenUNIX', 'connectUNIX']
