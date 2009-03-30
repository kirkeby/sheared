import os
import time
import random
import weakref

from sheared import Reactor
from sheared import TimeoutError

def in_reactor(expected_result):
    def outer(f):
        def inner():
            reactor = Reactor()
            reactor.start(f)
            if callable(expected_result):
                assert expected_result(reactor.result), \
                       repr(reactor.result)
            else:
                assert reactor.result == expected_result, \
                       '%r <> %r' % (reactor.result, expected_result,)
        return inner
    return outer

@in_reactor('ok')
def test_noop(reactor):
    reactor.result = 'ok'

@in_reactor(lambda (qux, ref): qux == 'root' and ref() is None)
def test_file(reactor):
    here = os.path.dirname(__file__)
    f = reactor.open(os.path.join(here, 'passwd'))
    reactor.result = f.read(4), weakref.ref(f)

@in_reactor(lambda result: round(result, 1) == 0.1)
def test_sleep(reactor):
    start = time.time()
    reactor.sleep(0.1)
    stop = time.time()
    reactor.result = stop - start

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

@in_reactor(['Hello, World!\r\n', '127.0.0.1:7\r\n', 'foo'])
def test_connect_tcp(reactor):
    t = reactor.connect('tcp:localhost:echo')
    t.write('Hello, World!\r\n')
    t.write('%s:%d\r\n' % t.peer)
    t.write('foo')
    t.shutdown(1)
    reactor.result = t.readlines()
    t.close()

port = int(random.random() * 8192 + 22000)
addr = 'tcp:localhost:%d' % port

@in_reactor('127.0.0.1:%d' % port)
def test_listen_tcp(reactor):
    def application(transport):
        transport.write('%s:%d' % transport.here)
        transport.close()
    reactor.listen(application, addr)

    t = reactor.connect(addr)
    reactor.result = t.read()
    t.close()

    reactor.stop()

@in_reactor('Ok')
def test_listen_tcp_timeout(reactor):
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

@in_reactor('Ok')
def test_block_notify(reactor):
    def one(o):
        reactor.result = reactor.block_on(o)
    def two(o, what):
        reactor.notify_on(o, what)

    reactor.spawn(one, (42,))
    reactor.spawn(two, (42, 'Ok'))

@in_reactor('Ok')
def test_block_notify_timeout(reactor):
    try:
        reactor.block_on(42, 0.1)
    except TimeoutError:
        reactor.result = 'Ok'
