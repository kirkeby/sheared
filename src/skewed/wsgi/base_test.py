from StringIO import StringIO
from skewed.wsgi import BaseWSGIServer

import logging
log = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter())
log.addHandler(handler)

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
        self.close = lambda: None
        self.shutdown = lambda i: None

class WSGIServer(BaseWSGIServer):
    def __init__(self, app):
        BaseWSGIServer.__init__(self)
        self.__application = app
    def find_application(self, host, path_info):
        return self.__application, '', path_info

def get_application(app, uri='/', headers=[]):
    req = 'GET %s HTTP/1.0\r\n' % uri
    for header in headers:
        req = req + header + '\r\n'
    req = req + '\r\n'

    transport = FakeTransport(req)
    server = WSGIServer(app)
    server(transport)
    return transport.output.getvalue()

def test_get():
    def app(env, start_response):
        start_response('200 Ok', [])
        return ['Hello, World!\r\n']
    
    assert get_application(app) == 'HTTP/1.0 200 Ok\r\n\r\n' 'Hello, World!\r\n'

def test_exception():
    def app(env, start_response):
        raise AssertionError, 'this always fails'

    try:
        log.setLevel(100)
        assert get_application(app).startswith('HTTP/1.0 500 Internal Server Error\r\n')
    finally:
        log.setLevel(0)
        

def test_http_env():
    def app(env, start_response):
        start_response('200 Ok', [])
        return ['HTTP_QUX: ' + env.get('HTTP_QUX', '')]

    assert get_application(app, headers=['Qux: FuBar']) == 'HTTP/1.0 200 Ok\r\n\r\n' \
                                         'HTTP_QUX: FuBar'

def test_http_headers():
    def app(env, start_response):
        start_response('200 Ok', [('Qux', 'quuuuux')])
        return ['']

    assert get_application(app) == 'HTTP/1.0 200 Ok\r\n' \
                             'Qux: quuuuux\r\n' \
                             '\r\n'

def test_bad_request():
    def app(env, start_response):
        start_response('200 Ok', [])
        return ['']

    log.setLevel(100)
    assert get_application(app, uri='') == \
           'HTTP/1.0 500 Bad Request\r\n' \
           'Content-Type: text/plain\r\n\r\n' \
           'Bad Request: GET  HTTP/1.0\r\n'
    log.setLevel(0)
