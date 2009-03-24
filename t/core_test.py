import time
import random
import weakref

from sheared import Reactor
from sheared import TimeoutError

def test_file():
    def run(reactor):
        f = reactor.open('/etc/passwd')
        reactor.file_ref = weakref.ref(f)
        reactor.qux = f.read(4)
    reactor = Reactor()
    reactor.start(run)
    assert reactor.qux == 'root'
    assert reactor.file_ref() is None

def test_noop():
    def run(reactor):
        pass

    reactor = Reactor()
    reactor.start(run)

def test_sleep():
    def run(reactor):
        start = time.time()
        reactor.sleep(0.1)
        stop = time.time()
        reactor.result = stop - start

    reactor = Reactor()
    reactor.start(run)
    assert round(reactor.result, 1) == 0.1

def test_stop():
    def sleeper(reactor):
        reactor.sleep(10.0)
    def run(reactor):
        reactor.spawn(sleeper, (reactor,))
        reactor.stop()

    reactor = Reactor()
    start = time.time()
    reactor.start(run)
    stop = time.time()

    assert round(stop - start, 1) == 0.0

def test_connect_tcp():
    def run(reactor):
        t = reactor.connect('tcp:localhost:echo')
        t.write('Hello, World!\r\n')
        t.write('%s:%d - %s:%d\r\n' % (t.here + t.peer))
        t.write('foo')
        t.shutdown(1)
        reactor.result = t.readlines()
        reactor.port = t.here[1]
        t.close()

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == ['Hello, World!\r\n',
                              '127.0.0.1:%d - 127.0.0.1:7\r\n' % reactor.port,
                              'foo']

port = int(random.random() * 8192 + 22000)
addr = 'tcp:localhost:%d' % port

def test_listen_tcp():
    def application(transport):
        transport.write('%s:%d - %s:%d' % (transport.here + transport.peer))
        transport.close()
    def run(reactor):
        reactor.listen(application, addr)
    
        t = reactor.connect(addr)
        reactor.ports = port, t.here[1]
        reactor.result = t.read()
        t.close()

        reactor.stop()

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == '127.0.0.1:%d - 127.0.0.1:%d' % reactor.ports

def test_listen_tcp_tieout():
    def run(reactor):
        def application(transport):
            reactor.sleep(60.0)
            transport.close()

        reactor.listen(application, addr)
    
        t = reactor.connect(addr)
        try:
            _ = t.read(8192, 0.1)
        except TimeoutError:
            reactor.result = 'Ok'
        else:
            reactor.result = 'Fail'
        t.close()

        reactor.stop()

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == 'Ok'
