# vim:tw=0:

from sheared.protocol import http

def test_no_accept_header():
    assert http.choose_content_type(None, ['text/html']) == 'text/html'

def test_accept_anything():
    assert http.choose_content_type('*/*', ['text/html']) == 'text/html'

def test_with_qval():
    assert http.choose_content_type('text/*; q=0.5, text/html; q=1.0',
                                    ['text/plain', 'text/html']) \
           == 'text/html'

    assert http.choose_content_type('text/html, */*; q=0.1',
                                    ['application/xhtml+xml', 'text/html']) \
           == 'text/html'

def test_unacceptable():
    try:
        http.choose_content_type('text/plain', ['text/html'])
    except http.NotAcceptable:
        pass
    else:
        raise AssertionError

def test_collision():
    assert http.choose_content_type('application/xhtml+xml,text/html',
                                    ['application/xhtml+xml', 'text/html']) \
           == 'application/xhtml+xml'
                                    
def test_fudging():
    assert http.choose_content_type('text/html, */*',
                                    ['application/xhtml+xml', 'text/html']) \
           == 'text/html'
