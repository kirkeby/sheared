#!/usr/bin/env python

import sys, os, time

from sheared import reactor
from sheared.protocol import echo
from sheared.protocol import basic
from sheared.python import daemonize

daemonize.daemonize()

#sys.stdout = open('/tmp/error.log', 'w')
#sys.stderr = sys.stdout
#sys.stderr.write('[%s] PID %d\n' % (time.ctime(), os.getpid()))

factory = basic.ProtocolFactory(reactor, echo.EchoServer)
reactor.listenTCP(factory, ('0.0.0.0', int(sys.argv[1])))
reactor.run()
