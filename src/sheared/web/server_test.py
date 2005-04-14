from sheared.web.server import HTTPServer
from sheared.web.virtualhost import VirtualHost
from sheared.web.mock import SimpleCollection, parseReply, StringTransport

def do_request(s, parse=1):
    server = HTTPServer()
    vh = VirtualHost(SimpleCollection('foo.com'))
    server.addVirtualHost('foo.com', vh)
    vh = VirtualHost(SimpleCollection('bar.com'))
    server.addVirtualHost('bar.com', vh)
    server.setDefaultHost('bar.com')

    transport = StringTransport()
    transport.appendInput(s)
    server.startup(transport)

    if parse:
        return parseReply(transport.getOutput())
    else:
        return transport.getOutput()

def test_PostUrlencodedRequest():
    status, headers, body = do_request(
        'POST /post HTTP/1.0\r\n'
        'Host: foo.com\r\n'
        'Content-Length: 12\r\n'
        'Content-Type: application/x-www-form-urlencoded\r\n'
        '\r\n'
        'q=fortytwo\r\n'
    )

    assert body == 'Welcome to foo.com!\r\n'
    assert status.version == (1, 0)
    assert status.code == 200

def test_PostFormdataRequest():
    status, headers, body = do_request(
           'POST /post HTTP/1.0\r\n'
           'Host: foo.com\r\n'
           'Content-Length: 89\r\n'
           'Content-Type: multipart/form-data; '
           '              boundary=foo\r\n'
           '\r\n'
           '--foo\r\n'
           'Content-Disposition: form-data; '
           '                     name=q\r\n'
           '\r\n'
           'fortytwo\r\n'
           '--foo--\r\n')

    assert body == 'Welcome to foo.com!\r\n'
    assert status.version == (1, 0)
    assert status.code == 200

def test_FullRequestWithFoo():
    status, headers, body = do_request('''GET / HTTP/1.0\r\nHost: foo.com\r\n\r\n''')
    
    assert status.version == (1, 0)
    assert status.code == 200
    assert body == 'Welcome to foo.com!\r\n'

def test_FullRequestWithBar():
    status, headers, body = do_request('''GET / HTTP/1.0\r\nHost: bar.com\r\n\r\n''')
    
    assert status.version == (1, 0)
    assert status.code == 200
    assert body == 'Welcome to bar.com!\r\n'

def test_FullRequestWithBlech():
    status, headers, body = do_request('''GET / HTTP/1.0\r\nHost: blech.com\r\n\r\n''')
    
    assert status.version == (1, 0)
    assert status.code == 200
    assert body == 'Welcome to bar.com!\r\n'

def test_FullRequestWithoutHost():
    status, headers, body = do_request('''GET / HTTP/1.0\r\n\r\n''')
    
    assert status.version == (1, 0)
    assert status.code == 200
    assert body == 'Welcome to bar.com!\r\n'

def test_SimpleRequest():
    assert do_request('''GET /''', parse=0) == 'Welcome to bar.com!\r\n'

def test_HeadRequest():
    status, headers, body = do_request('''HEAD / HTTP/1.0\r\n\r\n''')
    assert status.code == 200
    assert body == ''

def test_OldConditionalRequest():
    status, headers, body = do_request(
            'GET / HTTP/1.0\r\n'
            'If-Modified-Since: Sat, 07 Jul 1979 20:00:00 GMT\r\n'
            '\r\n')
    assert headers['Last-Modified'] == 'Sat, 07 Jul 1979 21:00:00 GMT'
    assert status.code == 200
    assert body == 'Welcome to bar.com!\r\n'

def test_CurrentConditionalRequest():
    status, headers, body = do_request(
            'GET / HTTP/1.0\r\n'
            'If-Modified-Since: Sat, 07 Jul 1979 21:00:00 GMT\r\n'
            '\r\n')
    assert headers['Last-Modified'] == 'Sat, 07 Jul 1979 21:00:00 GMT'
    assert status.code == 304
    assert body == ''

def test_NewConditionalRequest():
    status, headers, body = do_request(
            'GET / HTTP/1.0\r\n'
            'If-Modified-Since: Sat, 07 Jul 1979 22:00:00 GMT\r\n'
            '\r\n')
    assert headers['Last-Modified'] == 'Sat, 07 Jul 1979 21:00:00 GMT'
    assert status.code == 304
    assert body == ''

# FIXME
#def test_MassageReplyHeaders():
#    def foo(request, reply):
#        reply.headers.setHeader('Foo', 'fubar')
#
#    self.server.massageReplyHeadCallbacks.append(foo)
#    status, headers, body = do_request('''GET / HTTP/1.0\r\nHost: foo.com\r\n\r\n''')
#    self.reactor.start()
#
#    status, headers, body = parseReply(self.transport.getOutput())
#    
#    assert status.code == 200
#    assert body == 'Welcome to foo.com!\r\n'
#    assert headers['Content-Length'] == str(len(body))
#    assert headers['Content-Type'] == 'text/plain'
#    assert headers['Foo'] == 'fubar'

def test_ErrorMessage():
    status, headers, body = do_request('''GET /abuse-me HTTP/1.0\r\n\r\n''')
    
    assert status.code == 403
    assert body == 'Sod off, cretin!\r\n'
    assert headers['Content-Type'] == 'text/plain'
    assert headers['Content-Length'] == str(len(body))
    assert headers.keys() == ['Date', 'Content-Type', 'Content-Length']

def test_Redirect():
    status, headers, body = do_request('''GET /moved HTTP/1.0\r\n\r\n''')
    
    assert status.version == (1, 0)
    assert status.code == 301
    assert headers.has_key('Location') == 1
