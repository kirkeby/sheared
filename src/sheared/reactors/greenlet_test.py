import time

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
