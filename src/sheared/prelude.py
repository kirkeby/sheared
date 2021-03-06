import sys
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

class ReactorFile:
    def __init__(self, reactor, file): 
        self.reactor = reactor
        self.file = file
        self.fd = file.fileno()
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
        if self.file is None:
            return
        self.file.close()
        self.file = None
        self.reactor = None

class ReactorSocket(ReactorFile):
    def __init__(self, reactor, sock):
        ReactorFile.__init__(self, reactor, sock)

    def recv(self, max_bytes):
        return self.recvfrom(max_bytes)[1]

    def recvfrom(self, max_bytes):
        return self.reactor._recvfrom(self.file, max_bytes, None)

    def send(self, buffer):
        return self.reactor._send(self.file, buffer, None)
        
    def sendto(self, buffer, addr, flags=0):
        return self.reactor._sendto(self.file, buffer, flags, addr, None)

    def bind(self, addr):
        self.file.bind(addr)

    def connect(self, addr):
        self.file.connect(addr)
        # FIXME - Ehm, return when ready, i.e. readable, right?

    def shutdown(self, how):
        self.file.shutdown(how)

class dictolist(object):
    '''I am a dict'o'lists.'''
    def __init__(self):
        self.pairs = {}

    def keys(self):
        return self.pairs.keys()

    def __iter__(self):
        return iter(self.pairs)

    def __len__(self):
        return len(self.pairs)

    def append_to(self, key, item):
        if key not in self.pairs:
            self.pairs[key] = []
        self.pairs[key].append(item)

    def pop_from(self, key, i=0):
        v = self.pairs[key].pop(i)
        if not self.pairs[key]:
            del self.pairs[key]
        return v

    def remove_from(self, key, item):
        self.pairs[key].remove(item)
        if not self.pairs[key]:
            del self.pairs[key]
