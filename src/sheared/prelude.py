import os
from socket import getservbyname, AF_UNIX, AF_INET, SOCK_STREAM

def parse_address_uri(where):
    domain, address = where.split(':', 1)

    if domain == 'tcp':
        domain = AF_INET, SOCK_STREAM
        ip, port = address.split(':')
        if ip == '*':
            ip = ''
        try:
            port = int(port)
        except ValueError:
            port = getservbyname(port, 'tcp')
        address = ip, port

    elif domain == 'unix':
        domain = AF_UNIX, SOCK_STREAM

    else:
        raise 'Unknown domain: %s' % domain

    return domain, address

class ReactorFileCloser:
    '''I make sure the file you hand me is closed, when I am deleted.'''
    def __init__(self, file):
        self.file = file
    def __del__(self):
        if self.file is None:
            return
        if isinstance(self.file, int):
            os.close(self.file)
        else:
            self.file.close()
            self.file = None

class ReactorFile:
    def __init__(self, reactor, fd): 
        self.reactor = reactor
        self.closer = ReactorFileCloser(fd)
        self.fd = fd
        self.buffered = ''

    def read(self, max=None, timeout=None):
        if max is None:
            if timeout:
                raise NotImplementedError('Cannot slurp a file with a timeout')
            data, self.buffered = self.buffered, ''
            while 1:
                d = self.reactor._read(self.fd, 8192, None)
                if d == '':
                    break
                data = data + d
            return data
        elif self.buffered:
            data, self.buffered = self.buffered[:max], self.buffered[max:]
        else:
            data = self.reactor._read(self.fd, max, timeout)
        return data

    def readline(self):
        i = self.buffered.find('\n')
        while i < 0:
            d = self.reactor._read(self.fd, 8192, None)
            if d == '':
                i = len(self.buffered)
                break
            j = d.find('\n')
            if not j < 0:
                i = j + len(self.buffered)
            self.buffered = self.buffered + d

        data, self.buffered = self.buffered[:i+1], self.buffered[i+1:]
        return data

    def readlines(self):
        return [line for line in self]

    # iteration protocol
    def __iter__(self):
        return self
    def next(self):
        line = self.readline()
        if line == '':
            raise StopIteration
        else:
            return line

    def write(self, data):
        while data:
            i = self.reactor._write(self.fd, data, None)
            data = data[i:]

    def close(self):
        os.close(self.fd)
        self.reactor = None
        self.closer = None

class ReactorSocket(ReactorFile):
    def __init__(self, reactor, sock):
        self.reactor = reactor
        self.closer = ReactorFileCloser(sock)
        self.fd = sock.fileno()
        self.buffered = ''
        self.sock = sock
        self.here = self.sock.getsockname()
        self.peer = self.sock.getpeername()

    def shutdown(self, how):
        self.sock.shutdown(how)

    def close(self):
        self.sock.close()
        self.closer = None
        self.reactor = None

