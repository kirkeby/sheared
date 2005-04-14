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

def test_Unixtime():
    """Test HTTPDateTime against unixtime (seconds since epoch)."""
    d = http.HTTPDateTime(300229200)
    assert str(d), "Sat == 07 Jul 1979 21:00:00 GMT"
    c = http.HTTPDateTime(str(d))
    assert not c > d 
    assert not d > c

def test_Asctime():
    """Test HTTPDateTime against ANSI C's asctime date/time format."""
    d = http.HTTPDateTime("Sun Nov 6 08:49:37 1994")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"
    d = http.HTTPDateTime("Sun Nov  6 08:49:37 1994")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"

def test_RFC822():
    """Test HTTPDateTime against the RFC 822 date/time format."""
    d = http.HTTPDateTime("Sun, 06 Nov 1994 08:49:37 GMT")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"
    d = http.HTTPDateTime("Sun,   06 Nov 1994 08:49:37 GMT")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"

def test_RFC850():
    """Test HTTPDateTime against the RFC 850 date/time format."""
    d = http.HTTPDateTime("Sunday, 06-Nov-94 08:49:37 GMT")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"
    d = http.HTTPDateTime("Sunday, 06-Nov-94   08:49:37 GMT")
    assert str(d), "Sun == 06 Nov 1994 08:49:37 GMT"

def test_Comparison():
    s = http.HTTPDateTime(300000000)
    t = http.HTTPDateTime(300229200)
    u = http.HTTPDateTime(300300000)

    assert s < t
    assert t < u
    assert s < u

def test_Empty():
    """Test HTTPHeaders with no headers."""
    h = http.HTTPHeaders("")
    assert not len(h.items())

def test_Case():
    """Test HTTPHeaders with different cased headers and lookups."""
    h = http.HTTPHeaders("Header: value\r\n" + "some-Other-heAder: Some-Other-value\r\n")

    assert h.has_key('header')
    assert h.has_key('some-other-header')

    assert h.get('header') == 'value'
    assert h.get('header') == 'value'
    assert h['header'] == 'value'
    assert h['header'] == 'value'

    assert h.get('some-other-header') == 'Some-Other-value'
    assert h.get('SOME-otHer-header') == 'Some-Other-value'
    assert h['some-OtheR-header'] == 'Some-Other-value'
    assert h['some-other-heAder'] == 'Some-Other-value'

def test_SingleLine():
    """Test HTTPHeaders with single-line headers."""
    h = http.HTTPHeaders("Header: value")
    assert h['header'] == 'value'
    h = http.HTTPHeaders("Header: value ")
    assert h['header'] == 'value'
    h = http.HTTPHeaders("Header:  value")
    assert h['header'] == 'value'

def test_MultiLine():
    """Test HTTPHeaders with multi-line headers."""
    h = http.HTTPHeaders("Header: value\r\n\tand this too")
    assert h['header'] == 'value\tand this too'

def test_Multiple():
    """Test HTTPHeaders with multiple of the same headers."""
    h = http.HTTPHeaders("Header: value\r\nHeader: and this too")
    assert h['header'] == 'value, and this too'

    h = http.HTTPHeaders("Header: value, and this too")
    assert h['header'] == 'value, and this too'

def test_Items():
    """Test HTTPHeaders items method."""
    h = http.HTTPHeaders('One: \r\nTwo: \r\n')
    assert h.items() == [('One', ''), ('Two', '')]

def test_BadHeaders():
    """Test HTTPHeaders against some bad HTTP headers."""
    for bork in [" ", "\r\n Header: bar"]:
        # XMMS breaks this :(
        # "Header:"
        try:
            http.HTTPHeaders(bork)
        except ValueError:
            pass
        else:
            raise AssertionError

def test_Keys():
    """Test HTTPHeaders.keys."""
    h = http.HTTPHeaders("Foo: value\r\nBar: and this too")
    assert h.keys() == ['Foo', 'Bar']

def test_Del():
    """Test HTTPHeaders.delHeader."""
    h = http.HTTPHeaders("Foo: value\r\nBar: and this too")
    h.delHeader('Bar')
    assert h.keys() == ['Foo']

def test_SimpleRequest():
    """Test HTTPRequestLine against a simple HTTP request (version 0.9)."""
    r = http.HTTPRequestLine("GET /")
    assert r.version == (0, 9)
    assert r.method == 'GET'
    assert r.uri == ('', '', '/', '', '')

def test_FullRequest():
    """Test HTTPRequestLine against a full HTTP request."""
    r = http.HTTPRequestLine("GET / HTTP/11.209")
    assert r.version == (11, 209)
    assert r.method == 'GET'
    assert r.uri == ('', '', '/', '', '')

def test_BadRequestLine():
    """Test HTTPRequestLine against some bad HTTP request-lines."""
    for l in ["/", " GET /", "GET / HTTP/1.0 ", "GET\t/ HTTP/1.0", "GET /  HTTP/1.0"]:
        try:
            http.HTTPRequestLine(l)
        except ValueError:
            pass
        else:
            raise AssertionError, `l`
