from sheared.reactors.greenlet import Reactor

def test_read():
    def run(reactor):
        f = open('/etc/passwd')
        reactor.result = reactor.read(f.fileno(), 4)

    reactor = Reactor()
    reactor.start(run)
    assert reactor.result == 'root'
