from sheared.python.application import Application
from sheared.python.log import Log
from sheared.web.server import HTTPServer
from sheared.web.subserver import HTTPSubServer
from sheared.web.virtualhost import VirtualHost
from sheared import reactor

webserver_options = [
    ['set_str', 1, 'address', '', 'bind', 'webserver.bind',
     'Bind web server to this place.'],

    ['set_bool', 1, 'subserver', '', 'subserver', 'webserver.subserver',
     'Build a HTTPSubServer instead of a normal HTTPServer.'],

    ['set_str', 1, 'hostname', '', 'hostname', 'webserver.hostname',
     'Externally visible name of web server.'],

    ['set_str', 1, 'accesslog', '', 'access-log', 'webserver.access-log',
     'Path of web-server access log.'],

    ['set_str', 1, 'errorlog', '', 'error-log', 'webserver.error-log',
     'Path of web-server error log.'],
]

class WebserverApplication(Application):
    def __init__(self, name='webserver', options=[]):
        self.port = 80
        self.interface = ''
        self.hostname = 'localhost'

        self.subserver = 0

        self.accesslog = None
        self.errorlog = None

        opts = []
        opts.extend(webserver_options)
        opts.extend(options)

        Application.__init__(self, name, opts)

    def configure(self):
        raise NotImplementedError

    def setup(self):
        if self.subserver:
            self.webserver = HTTPSubServer()
        else:
            self.webserver = HTTPServer()
        self.webserver.setDefaultHost(self.hostname)

        if self.accesslog:
            self.webserver.setAccessLog(Log(self.accesslog))
        if self.errorlog:
            self.webserver.setErrorLog(Log(self.errorlog))

        root = self.configure()
        if root:
            self.vhost = VirtualHost(root)
            self.webserver.addVirtualHost(self.hostname, self.vhost)

        reactor.listen(self.webserver, self.address)
