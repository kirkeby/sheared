# vim:nowrap:textwidth=0

from sheared.protocol import basic
from sheared.protocol import http

def sendRequest(reactor, path, request, reply):
    """Pass a HTTP request off to a sub-server listening on path."""

    fd = reactor.open(path, 'w')
    reactor.write(fd, 'Hello, World!')
    reactor.close(fd)

def HTTPSubServer(protocol.Basic):
    def run(self):
        
def recvRequest(reactor):
    
