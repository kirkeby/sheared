# vim:nowrap:textwidth=0

import random

class StringTransport:
    def __init__(self, input):
        self.input = input
        self.output = ''
        self.closed = 0

    def read(self, cnt=4096):
        if self.closed:
            raise IOError, 'cannot do I/O on a closed Transport'
        cnt = min(cnt, 1 + int(random.random() * (len(self.input) - 1)))
        data = self.input[:cnt]
        self.input = self.input[cnt:]
        return data
    def write(self, data):
        if self.closed:
            raise IOError, 'cannot do I/O on a closed Transport'
        self.output = self.output + data
        return len(data)

    def close(self):
        if self.closed:
            raise IOError, 'cannot do I/O on a closed Transport'
        self.closed = 1

    def received(self):
        return self.output

class ReactorTransport:
    def __init__(self, reactor, file, other):
        self.reactor = reactor
        self.file = file
        self.other = other

        self.reactor.prepareFile(self.file)

    def read(self, max=4096):
        return self.reactor.read(self.file, max)
    def write(self, data):
        self.reactor.write(self.file, data)

    def close(self):
        self.file.close()
