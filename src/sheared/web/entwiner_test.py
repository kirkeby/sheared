from sheared.web import entwiner
from sheared.web.mock import FakeReply, FakeRequest
from sheared import error

import os.path
foo_html = os.path.join(os.path.dirname(__file__), 'test-docroot', 'foo.html')

def test_TemplatePages():
    class Foo(entwiner.Entwiner):
        template_pages = [foo_html]
        def entwine(self, request, reply, subpath):
            self.context['foo'] = 'foo'
    ent = Foo()
    req = FakeRequest()
    rep = FakeReply()
    ent.handle(req, rep, None)
    assert rep.sent == 'foo'

def test_RequestContext():
    class FooEntwiner(entwiner.Entwiner):
        template_pages = [foo_html]
        def entwine(self, request, reply, subpath):
            pass

    request = FakeRequest()
    request.context = {'foo': 'fubar'}
    reply = FakeReply()

    foo = FooEntwiner()
    foo.handle(request, reply, '')
    
    assert reply.sent == 'fubar'

def test_ConditionalGet():
    class FooEntwiner(entwiner.Entwiner):
        template_pages = [foo_html]
        def entwine(self, request, reply, subpath):
            pass

    # test with no match
    request = FakeRequest()
    request.context = {'foo': 'fubar'}
    request.headers.setHeader('If-None-Match', 'abc')
    reply = FakeReply()

    foo = FooEntwiner()
    foo.handle(request, reply, '')
    
    assert reply.status == 200
    assert reply.sent == 'fubar'

    # test with match
    request.headers.setHeader('If-None-Match', reply.headers['ETag'])
    reply = FakeReply()

    try:
        foo.handle(request, reply, '')
    except error.web.NotModified:
        pass
    else:
        raise AssertionError
    assert reply.sent == ''

def test_ContentLength():
    class FooEntwiner(entwiner.Entwiner):
        template_pages = [foo_html]
        def entwine(self, request, reply, subpath):
            pass

    # test with no match
    request = FakeRequest()
    request.context = {'foo': 'fubar'}
    reply = FakeReply()

    foo = FooEntwiner()
    foo.handle(request, reply, '')
    
    assert reply.status == 200
    assert reply.sent == 'fubar'
    assert reply.headers['content-length'] == str(len(reply.sent))

