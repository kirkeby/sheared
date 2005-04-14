import os
import random

def _test_request():
    try:
        os.unlink('./test/fifoo')
    except:
        pass

    self.port = int(random.random() * 8192 + 22000)
        
    self.reactor = reactor

    factory = subserver.HTTPSubServer()

    vh = virtualhost.VirtualHost(SimpleCollection('localhost'))
    factory.addVirtualHost('localhost', vh)
    factory.setDefaultHost('localhost')
    self.reactor.listenUNIX(factory, './test/fifoo')

    factory = server.HTTPServer()
    vhost = virtualhost.VirtualHost(subserver.HTTPSubServerCollection('./test/fifoo'))
    factory.addVirtualHost('localhost', vhost)
    factory.setDefaultHost('localhost')
    self.reactor.listenTCP(factory, ('127.0.0.1', self.port))

    def f():
        try:
            argv = ['/bin/sh', '-c',
                    'curl -D - '
                    'http://localhost:%d/ 2>/dev/null' % self.port]
            reply = commands.getoutput(argv[0], argv)
            status, headers, body = parseReply(reply)
        
            self.assertEquals(status.version, (1, 0))
            self.assertEquals(status.code, 200)
            self.assertEquals(body, 'Welcome to localhost!\r\n')

        finally:
            self.reactor.stop()

    self.reactor.createtasklet(f)
    self.reactor.start()

