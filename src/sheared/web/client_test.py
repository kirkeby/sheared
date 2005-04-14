import random

from sheared.web import virtualhost
from sheared.web import client
from sheared.web import server
from sheared import reactor

from sheared.web.mock import SimpleCollection

class TestGetContent:
    def setUp(self):
        self.port = int(random.random() * 8192 + 22000)

        coll = SimpleCollection('localhost')
        vhost = virtualhost.VirtualHost(coll)
        srv = server.HTTPServer()
        srv.addVirtualHost('localhost', vhost)
        srv.setDefaultHost('localhost')

        reactor.listenTCP(srv, ('127.0.0.1', self.port),
                          max_client_count=1)

    # FIXME
    def _test_get_content(self):
        def run():
            self.content = client.get_content('http://127.0.0.1:%d/' % (self.port))

        reactor.spawn(run)
        reactor.start()
        assert content == 'Welcome to localhost!\r\n'
