#!/usr/bin/env python

import sys

from sheared import reactor
from sheared.protocol import echo
from sheared.protocol import basic

factory = basic.ProtocolFactory(echo.EchoServer)
reactor.listenTCP(factory, ('0.0.0.0', int(sys.argv[1])))
reactor.run()
