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
        self.buffered = ['']
        self.file = file
        self.newline = newline

    def read(self):
        if self.buffered:
            data = self.newline.join(self.buffered)
            self.buffered = ['']
        else:
            data = self.file.read()
        return data

    def readline(self):
        while len(self.buffered) == 1:
            read = self.file.read()
            if read == '':
                break
            lines = read.split(self.newline)
            self.buffered[-1] = self.buffered[-1] + lines[0]
            self.buffered.extend(lines[1:])

        line = self.buffered.pop(0)
        if self.buffered:
            line = line + self.newline
        return line
