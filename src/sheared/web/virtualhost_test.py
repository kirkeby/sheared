from sheared.web.virtualhost import VirtualHost
from sheared import error

from sheared.web.mock import FakeRequest, FakeReply, SimpleCollection

coll = SimpleCollection('foo')
virtualhost = VirtualHost(SimpleCollection('foo'))
    
def test_NormalGet():
    request = FakeRequest('GET / HTTP/1.0')
    reply = FakeReply()
    virtualhost.handle(request, reply)
    assert reply.status == 200
    assert reply.sent == 'Welcome to foo!\r\n'

def test_RedirectWithoutHostHeader():
    request = FakeRequest('GET /moved HTTP/1.0')
    reply = FakeReply()
    try:
        virtualhost.handle(request, reply)
    except error.web.Moved:
        pass
    else:
        raise AssertionError
    assert reply.headers['Location'] == 'http://foo.com/'

def test_RedirectWithHostHeader():
    request = FakeRequest('GET /moved HTTP/1.0', 'Host: foo.com\r\n')
    reply = FakeReply()
    try:
        virtualhost.handle(request, reply)
    except error.web.Moved:
        pass
    else:
        raise AssertionError
    assert reply.headers['Location'] == 'http://foo.com/'
