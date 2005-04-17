from skewed.wsgi.misc import IEAcceptHack
from skewed.wsgi.base_test import get_application

user_agents = [
    'User-Agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
    'User-Agent: Googlebot/2.1 (+http://www.google.com/bot.html)',
]

def test_ie_hack():
    def app(environ, start_response):
        start_response('200 Ok', [('Content-Type', 'application/xhtml+xml')])
        return []
    hacked_app = IEAcceptHack(app)
    assert get_application(hacked_app) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: application/xhtml+xml\r\nVary: User-Agent\r\n\r\n'
    assert get_application(hacked_app, headers=[user_agents[0]]) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: text/html\r\nVary: User-Agent\r\n\r\n'
    assert get_application(hacked_app, headers=[user_agents[1]]) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: text/html\r\nVary: User-Agent\r\n\r\n'

def test_ie_hack_with_params():
    def app(environ, start_response):
        ct = 'application/xhtml+xml; charset=utf-8'
        start_response('200 Ok', [('Content-Type', ct)])
        return []
    hacked_app = IEAcceptHack(app)
    assert get_application(hacked_app) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: application/xhtml+xml; charset=utf-8\r\nVary: User-Agent\r\n\r\n'
    assert get_application(hacked_app, headers=[user_agents[0]]) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\nVary: User-Agent\r\n\r\n'
    assert get_application(hacked_app, headers=[user_agents[1]]) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: text/html; charset=utf-8\r\nVary: User-Agent\r\n\r\n'

def test_ie_hack_with_vary_accept():
    def app(environ, start_response):
        start_response('200 Ok', [('Content-Type', 'application/xhtml+xml'),
                                  ('Vary', 'Accept'),])
        return []
    hacked_app = IEAcceptHack(app)
    assert get_application(hacked_app) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: application/xhtml+xml\r\nVary: Accept User-Agent\r\n\r\n'

def test_ie_hack_with_vary_ua():
    def app(environ, start_response):
        start_response('200 Ok', [('Content-Type', 'application/xhtml+xml'),
                                  ('Vary', 'User-Agent'),])
        return []
    hacked_app = IEAcceptHack(app)
    assert get_application(hacked_app) \
           == 'HTTP/1.0 200 Ok\r\nContent-Type: application/xhtml+xml\r\nVary: User-Agent\r\n\r\n'
