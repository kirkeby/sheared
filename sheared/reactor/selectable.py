# vim:nowrap:textwidth=0
import stackless, sys, fcntl, socket, os, errno, select, types, traceback

from sheared.reactor import transport

class ReactorFile:
    def __init__(self, fd):
        self.fd = fd
    def fileno(self):
        return self.fd
    def close(self):
        os.close(self.fd)

class ReactorShutdown(Exception):
    pass

class Reactor:
    def shutdown(self):
        self.stop = 1

    def buildselectable(self):
        r, w = [], []
        for fd, (handler, file, channel, argv) in self.waiting.items():
            if handler in [self.handleread, self.handleaccept]:
                r.append(fd)
            elif handler in [self.handlewrite, self.handleconnect]:
                w.append(fd)
            else:
                raise InternalError, ('unknown handler', handler)
        return r, w, r + w

    def flushunselectabels(self, r, w):
        try:
            for fd in r:
                select.select([fd], [], [], 0)
            for fd in w:
                select.select([], [fd], [], 0)
        except select.error, why:
            handler, file, channel, argv = self.waiting[fd]
            del self.waiting[fd]
            channel.send_exception(select.error, why)
        
    def handleread(self, file, channel, (max)):
        del self.waiting[file.fileno()]
        channel.send(os.read(file.fileno(), max))

    def handlewrite(self, file, channel, argv):
        count = os.write(file.fileno(), argv)
        argv = argv[count :]
        if argv:
            self.waiting[file.fileno()] = self.handlewrite, file, channel, argv
        else:
            del self.waiting[file.fileno()]
            channel.send(None)
            
    def handleaccept(self, file, channel, argv):
        sock, addr = file.accept()
        del self.waiting[file.fileno()]
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        channel.send((sock, addr))

    def handleconnect(self, file, channel, argv):
        del self.waiting[file.fileno()]
        err = file.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if err:
            channel.send(socket.error(err, os.strerror(err)))
        else:
            channel.send(None)

    def wait(self, file, op, argv):
        channel = self.tasklet_channel[stackless.getcurrent()]
        self.waiting[file.fileno()] = op, file, channel, argv
        return channel.receive()
    
    def accept(self, factory, sock):
        try:
            while 1:
                fd, addr = self.wait(sock, self.handleaccept, ())
                t = transport.ReactorTransport(self, fd, addr)
                self.createtasklet(factory.startup, (t,))

        finally:
            try:
                self.close(sock)
            except:
                traceback.print_exc()

    def connectSocket(self, family, type, addr):
        sock = socket.socket(family, type)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        #if not self.from_address is None:
        #    self.socket.bind(self.from_address)
    
        try:
            sock.connect(addr)
        except socket.error, (eno, _):
            if not eno == errno.EINPROGRESS:
                raise

        self.wait(sock, self.handleconnect, ())
        return transport.ReactorTransport(self, sock, addr)

    ### public reactor interface ###
    def __init__(self):
        self.tasklet = stackless.tasklet()

        self.tasklet_channel = {}

        self.waiting = {}

        self.started = 0
        self.stopped = 0
        self.stop = 0

    def start(self):
        self.started = 1
        self.tasklet.become()

        try:
            while not self.stop:
                while stackless.getruncount() > 1:
                    stackless.schedule()

                r, w, e = self.buildselectable()
                if not (r or w or e):
                    break

                try:
                    r, w, e = select.select(r, w, e)
                except select.error, (eno, emsg):
                    self.flushunselectabels(r, w)

                fds = r + w
                for fd in e:
                    if not fd in fds:
                        fds.append(fd)

                for fd in fds:
                    handler, file, channel, argv = self.waiting[fd]
                    try:
                        handler(file, channel, argv)
                    except socket.error, (eno, estr):
                        if not eno in (errno.EINTR, errno.EAGAIN):
                            channel.send(sys.exc_info()[1])
                    except:
                        channel.send(sys.exc_info()[1])

        finally:
            self.stopped = 1
            self.exc_info = sys.exc_info()

    def run(self):
        if not stackless.getmain() is stackless.getcurrent():
            raise RuntimeError, 'reactor not started from main tasklet'
        if not self.started:
            self.start()
        if self.stopped:
            raise RuntimeError, 'reactor already stopped'
        stackless.run()

    def createtasklet(self, func, args=(), kwargs={}):
        t = stackless.tasklet()
        c = stackless.channel()
        self.tasklet_channel[t] = c

        t.become(c)
        try:
            apply(func, args, kwargs)
        except:
            traceback.print_exc()

        del self.tasklet_channel[t]

    def open(self, path, mode):
        f = open(path, mode)
        fcntl.fcntl(f.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        return f

    def prepareFile(self, file):
        if isinstance(file, types.IntType):
            file = ReactorFile(file)
        fcntl.fcntl(file.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        return file

    def read(self, file, max=4096):
        return self.wait(file, self.handleread, (max))

    def write(self, file, data):
        return self.wait(file, self.handlewrite, (data))

    def close(self, file):
        file.close()

    def connectTCP(self, addr):
        return self.connectSocket(socket.AF_INET, socket.SOCK_STREAM, addr)
    def connectUNIX(self, addr):
        return self.connectSocket(socket.AF_UNIX, socket.SOCK_STREAM, addr)

    def listenTCP(self, factory, addr, backlog=5):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fcntl.fcntl(sock.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        # we do not want 'address already in use' because of TCP-
        # connections in TIME_WAIT state
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        sock.bind(addr)
        sock.listen(backlog)

        self.createtasklet(self.accept, (factory, sock))
