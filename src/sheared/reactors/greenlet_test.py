import time
import random

from sheared.reactors.greenlet import Reactor

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

def test_read():
    def run(reactor):
        f = open('/etc/passwd')
        reactor.result = reactor.read(f.fileno(), 4)

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == 'root'

def test_connect_tcp():
    def run(reactor):
        t = reactor.connect('tcp:localhost:echo')
        t.write('Hello, World!\r\n')
        t.write('qux\r\n')
        t.write('foo')
        t.shutdown(1)
        reactor.result = t.readlines()

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == ['Hello, World!\r\n',
                              'qux\r\n',
                              'foo']

def test_listen_tcp():
    def application(transport):
        transport.write('42')
        transport.close()
    def run(reactor):
        port = int(random.random() * 8192 + 22000)
        addr = 'tcp:localhost:%d' % port
        reactor.listen(application, addr)
    
        t = reactor.connect(addr)
        reactor.result = t.read()
        t.close()

        reactor.stop()

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == '42'
