from sheared import error

from sheared.web.resource import MovedResource, AliasedResource
from sheared.web.collections.static import StaticCollection
from sheared.web.virtualhost import VirtualHost

from sheared.web.mock import FakeRequest, FakeReply, FakeResource

# class MovedResourceTestCase(unittest.TestCase):
def test_Shallow():
    request = FakeRequest('GET /foo HTTP/1.0')
    reply = FakeReply()

    coll = MovedResource('bar')
    try:
        coll.handle(request, reply, '')
    except error.web.MovedPermanently:
        pass
    else:
        raise AssertionError
    assert reply.headers['location'] == 'bar'

def test_Deep():
    request = FakeRequest('GET /fubar HTTP/1.0')
    reply = FakeReply()

    coll = MovedResource('fu')
    coll = coll.getChild(request, reply, 'bar')
    try:
        coll.handle(request, reply, '')
    except error.web.MovedPermanently:
        pass
    else:
        raise AssertionError
    assert reply.headers['location'] == 'fu/bar'

# class AliasedResourceTestCase(unittest.TestCase):
def test_Get():
    request = FakeRequest('GET /alias HTTP/1.0')
    reply = FakeReply()

    orig = FakeResource()
    alias = AliasedResource(orig, 'real')
    coll = StaticCollection()
    coll.bind('real', orig)
    coll.bind('alias', alias)
    vh = VirtualHost(coll)

    vh.handle(request, reply)
    
    assert reply.status == 200
    assert reply.headers.has_key('Location') == 1
    assert reply.headers['Location'] == 'real'
    assert reply.headers['Content-Type'] == 'text/plain'
    assert reply.sent == 'Welcome to foo!\r\n'
