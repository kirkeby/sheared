# vim:tw=0:

from sheared.protocol import http

def test_no_accept_header():
    assert http.choose_content_type(None, [(1, 'text/html')]) == 1

def test_accept_anything():
    assert http.choose_content_type('*/*', [(1, 'text/html')]) == 1

def test_with_qval():
    assert http.choose_content_type('text/*; q=0.5, text/html; q=1.0',
                                    [(1, 'text/plain'), (2, 'text/html')]) \
           == 2

    assert http.choose_content_type('text/html, */*; q=0.1',
                                    [(1, 'application/xhtml+xml'), (2, 'text/html')]) \
           == 2

def test_unacceptable():
    assert http.choose_content_type('text/plain', [(1, 'text/html')]) == None

def test_collision():
    assert http.choose_content_type('application/xhtml+xml,text/html',
                                    [(1, 'application/xhtml+xml'), (2, 'text/html')]) \
           == 1
                                    
def test_fudging():
    assert http.choose_content_type('text/html, */*',
                                    [(1, 'application/xhtml+xml'), (2, 'text/html')]) \
           == 2
