from StringIO import StringIO
from skewed.wsgi import BaseWSGIServer

class FakeTransport:
    def __init__(self, input):
        self.here = 'localhost', 80
        self.there = 'localhost', 1234
        self.input = StringIO(input)
        self.output = StringIO()
        self.read = self.input.read
        self.readline = self.input.readline
        self.readlines = self.input.readlines
        self.write = self.output.write
        self.writelines = self.output.writelines

class WSGIServer(BaseWSGIServer):
    def __application(self, env, start_response):
        start_response('200 Ok', [('Content-Type', 'text/plain')])
        return ['Hello, World!\r\n']
    def find_application(self, host, path_info):
        return self.__application, '', path_info
    
def test_get():
    transport = FakeTransport('GET / HTTP/1.0\r\n\r\n')
    server = WSGIServer()
    server(transport)
    
    assert transport.output.getvalue() == '200 Ok\r\n' \
                                          'Content-Type: text/plain\r\n' \
                                          '\r\n' \
                                          'Hello, World!\r\n'
