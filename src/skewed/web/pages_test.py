# vim:tw=0

from skewed.wsgi.base_test import get_application
from skewed.web.pages import Pages

import os

app_root = os.path.join(os.path.dirname(__file__), 'test-application')

pages = Pages(None)
pages.pages_path = os.path.join(app_root, 'pages')
pages.templates_path = os.path.join(app_root, 'templates')

def test_index():
    result = get_application(pages)
    assert type(result) is str
    assert result == 'HTTP/1.0 200 Ok\r\n' 'Content-Type: text/xml; charset=utf-8\r\n\r\n' '<page>/index</page>'

    #result = get_application(pages, uri='/index')
    #assert result.split('\r\n')[-1] == '<pages>/qux</pages>'

    #result = get_application(pages, uri='/index/qux')
    #assert result.split('\r\n')[-1] == '<pages>/qux</pages>'
