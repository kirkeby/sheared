from sheared.python.application import Application
from sheared.web.server import HTTPServer
from sheared.web.virtualhost import VirtualHost
from sheared import reactor

webserver_options = [
    ['set_str', 1, 'address', '', 'bind', 'webserver.bind',
     'Bind web server to this place.'],

    ['set_str', 1, 'hostname', '', 'hostname', 'webserver.hostname',
     'Externally visible name of web server.'],
]

class WebserverApplication(Application):
    def __init__(self, name='webserver', options=[]):
        self.port = 80
        self.interface = ''
        self.hostname = 'localhost'

        opts = []
        opts.extend(webserver_options)
        opts.extend(options)

        Application.__init__(self, name, opts)

    def configure(self):
        raise NotImplementedError

    def setup(self):
        if self.port == 80:
            l = 'http://%s/' % self.hostname
        else:
            l = 'http://%s:%d/' % (self.hostname, self.port)
        self.root = self.configure()
        self.vhost = VirtualHost(self.root, l)

        self.webserver = HTTPServer()
        self.webserver.addVirtualHost(self.hostname, self.vhost)
        self.webserver.setDefaultHost(self.hostname)

        reactor.listen(self.webserver, self.address)
