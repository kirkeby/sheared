from StringIO import StringIO
from one_x import HTTPReply

class FakeHTTPServer:
    massageReplyHeadCallbacks = []

def test_status_int():
    transport = StringIO()
    reply = HTTPReply(FakeHTTPServer, None, transport, (1, 0))
    reply.status = 200
    reply.sendHead()

    assert transport.getvalue().startswith('HTTP/1.0 200 OK\r\n')


