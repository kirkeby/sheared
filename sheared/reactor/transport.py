# vim:nowrap:textwidth=0

class Transport:
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

