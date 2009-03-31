from sheared import Reactor
from os import kill, getpid
from signal import SIGHUP
from core_test import in_reactor

@in_reactor('ok')
def test_signal_reception(reactor):
    def callback(signal):
        reactor.result = 'ok'

    reactor.result = 'not ok'
    reactor.signal(SIGHUP, callback)
    kill(getpid(), SIGHUP)

