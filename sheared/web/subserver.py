import pickle

from sheared import reactor
from sheared.web import server
from sheared.python import fdpass

class HTTPSubServerCollection:
    isWalkable = 0

    def __init__(self, path):
        self.path = path

    def handle(self, request, reply, subpath):
        transport = reactor.current.connectUNIX(self.path)
        fdpass.send(transport.fileno(), reply.transport.fileno(), pickle.dumps(reply.transport.other))
        pickle.dump((request, subpath), transport)
        transport.close()

class HTTPSubServer(server.HTTPServer):
    def startup(self, transport):
        for i in range(3):
            try:
                sock, addr = fdpass.recv(transport.fileno())
                break
            except:
                pass
        else:
            raise
        addr = pickle.loads(addr)

        data = ''
        read = None
        while not read == '':
            read = transport.read()
            data = data + read
        transport.close()
        request, subpath = pickle.loads(data)

        transport = reactor.current.createTransport(sock, addr)
        reply = server.HTTPReply(request.version, transport)
        self.handle(request, reply)

__all__ = ['HTTPSubServerAdapter', 'HTTPSubServer']
