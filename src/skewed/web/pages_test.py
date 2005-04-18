# vim:tw=0

from skewed.wsgi.base_test import get_application
from skewed.web.pages import Pages

import os
import warnings
warnings.filterwarnings('ignore', 'Could not load .*')

app_root = os.path.join(os.path.dirname(__file__), 'test-application')

pages = Pages(None)
pages.pages_path = os.path.join(app_root, 'pages')
pages.templates_path = os.path.join(app_root, 'templates')
pages.static_path = os.path.join(app_root, 'static')
pages.load_templates()

def test_index():
    result = get_application(pages)
    assert type(result) is str
    assert result == 'HTTP/1.0 200 Ok\r\n' 'Content-Type: text/xml; charset=utf-8\r\n\r\n' "<?xml version='1.0' encoding='utf-8'?>\r\n" '<page></page>'

    result = get_application(pages, uri='/index')
    assert result.split('\r\n')[-1] == '<page></page>'

    result = get_application(pages, uri='/index/qux')
    assert result.split('\r\n')[-1] == '<page>/qux</page>'

def test_qux():
    result = get_application(pages, uri='/qux')
    assert type(result) is str
    assert result == 'HTTP/1.0 200 Ok\r\n' 'Content-Type: application/xhtml+xml; charset=utf-8\r\n\r\n' "<?xml version='1.0' encoding='utf-8'?>\r\n" '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\r\n' '          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\r\n' '<html>\n<body>\n<div>Hello, World!</div>\n</body>\n</html>'

def test_static():
    result = get_application(pages, uri='/blech')
    assert type(result) is str
    assert result == "HTTP/1.0 200 Ok\r\nContent-Type: text/xml\r\nVary: Accept\r\n\r\n<?xml version='1.0'?>\n<page>Qux</page>\n"

    result = get_application(pages, uri='/blech/qux')
    assert type(result) is str
    assert result == "HTTP/1.0 200 Ok\r\nContent-Type: text/xml\r\nVary: Accept\r\n\r\n<?xml version='1.0'?>\n<page>Qux</page>\n"