# vim:tw=0:

from skewed.wsgi.misc import choose_widget

def test_no_accept_header():
    environ = {}
    widgets = [ (1, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 1

def test_accept_anything():
    environ = { 'HTTP_ACCEPT': '*/*' }
    widgets = [ (1, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 1

def test_with_explicit_qval():
    environ = { 'HTTP_ACCEPT': 'text/*; q=0.5, text/html; q=1.0' }
    widgets = [ (1, {'Content-Type': 'text/plain'}),
                (2, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 2

def test_with_implicit_qval():
    environ = { 'HTTP_ACCEPT': 'text/html, */*; q=0.1', }
    widgets = [ (1, {'Content-Type': 'application/xhtml+xml'}),
                (2, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 2

def test_unacceptable():
    environ = { 'HTTP_ACCEPT': 'text/plain', }
    widgets = [ (1, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == None

def test_collision():
    environ = { 'HTTP_ACCEPT': 'application/xhtml+xml,text/html' }
    widgets = [ (1, {'Content-Type': 'application/xhtml+xml'}),
                (2, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 1
                                    
def test_fudging():
    environ = { 'HTTP_ACCEPT': 'text/html, */*' }
    widgets = [ (1, {'Content-Type': 'application/xhtml+xml'}),
                (2, {'Content-Type': 'text/html'}), ]
    assert choose_widget(environ, widgets) == 2
