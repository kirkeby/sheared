#!/usr/bin/env python

import sys, traceback

from sheared import reactor
from sheared.protocol import echo
from sheared.protocol import basic
from sheared.python import coroutine

try:
    factory = basic.ProtocolFactory(echo.EchoServer)
    reactor.listenTCP(factory, ('0.0.0.0', int(sys.argv[1])))
    reactor.run()
except coroutine.CoroutineReturned:
    print 'nothing more to do'
except coroutine.CoroutineFailed, (c, exc_info):
    apply(traceback.print_exception, exc_info)
except:
    apply(traceback.print_exception, sys.exc_info())

