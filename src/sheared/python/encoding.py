import encodings

class Encoding:
    def __init__(self, name):
        self.qux = encodings.search_function(name)
    def encode(self, text):
        return self.qux[0](text)[0]
    def decode(self, text):
        return self.qux[1](text)[0]
        
utf8 = Encoding('utf8')

del encodings
