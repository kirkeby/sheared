from sheared import reactor

def readfile(path):
    f = reactor.current.open(path, 'r')
    all = ''
    while 1:
        read = reactor.current.read(f, 4096)
        if read == '':
            break
        all += read
    reactor.current.close(f)
    return all

class Drainer:
    def __init__(self, file):
        self.file = file

    def read(self):
        data = ''
        read = None
        while not read == '':
            read = self.file.read()
            data = data + read
        return data

class RecordReader:
    def __init__(self, file, newline):
        self.buffered = ''
        self.file = file
        self.newline = newline

    def read(self):
        if self.buffered:
            data, self.buffered = self.buffered, ''
        else:
            data = self.file.read()
        return data

    def readline(self):
        while self.buffered.find(self.newline) < 0:
            data = self.file.read()
            if data == '':
                break
            self.buffered = self.buffered + data

        i = self.buffered.find(self.newline)
        if i < 0:
            data, self.buffered = self.buffered, ''
        else:
            data = self.buffered[ : i + len(self.newline)]
            self.buffered = self.buffered[i + len(self.newline) : ]
        
        return data
