# vim:nowrap:textwidth=0

import random, os, types

class StringTransport:
    def __init__(self):
        self.input = ''
        self.output = ''
        self.closed = 0

    def read(self, cnt=4096):
        cnt = min(cnt, 1 + int(random.random() * (len(self.input) - 1)))
        data = self.input[:cnt]
        self.input = self.input[cnt:]
        return data

    def write(self, data):
        if self.closed:
            raise IOError, 'cannot write to a closed Transport'
        self.output = self.output + data
        return len(data)

    def sendfile(self, file):
        d = file.read()
        while not d == '':
            self.output = self.output + d
            d = file.read()

    def close(self):
        if self.closed:
            raise IOError, 'already closed'
        self.closed = 1

    def appendInput(self, data):
        self.input = self.input + data
    def getOutput(self):
        return self.output

class FileTransport:
    def __init__(self, reactor, file, other):
        self.file = file
        if isinstance(file, types.IntType):
            self.fileno = file
        else:
            self.fileno = file.fileno()

    def read(self, max=4096):
        return os.read(self.fileno, max)
    def write(self, data):
        while data:
            cnt = os.write(self.fileno, data)
            data = data[cnt:]
    def close(self):
        os.close(self.fileno)

class ReactorTransport:
    def __init__(self, reactor, file, other):
        self.reactor = reactor
        self.file = self.reactor.prepareFile(file)
        self.other = other
        self.closed = 0

    def read(self, max=4096):
        return self.reactor.read(self.file, max)
    def write(self, data):
        self.reactor.write(self.file, data)
    def sendfile(self, file):
        self.reactor.sendfile(file, self.file)

    def fileno(self):
        return self.reactor.getfd(self.file)

    def close(self):
        self.reactor.close(self.file)
        self.closed = 1
