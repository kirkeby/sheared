from skewed.wsgi.misc import relative

def test_relative():
    # http://127.0.0.1/bar
    env = {
        'wsgi.url_scheme': 'http',
        'SERVER_NAME': '127.0.0.1',
        'SERVER_PORT': '80',
        'SCRIPT_NAME': '/bar',
        'PATH_INFO': '',
    }
    assert relative('qux', env) == 'http://127.0.0.1/bar/qux'
    assert relative('../qux', env) == 'http://127.0.0.1/qux'
