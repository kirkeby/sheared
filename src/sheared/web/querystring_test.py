from sheared import error

from sheared.web import querystring

def assertRaises(ex, f, *args, **kwargs):
    try:
        f(*args, **kwargs)
    except ex:
        pass
    else:
        raise AssertionError

#class HTTPQueryStringTestCase(unittest.TestCase):
qs = querystring.HTTPQueryString('int=1&hex=babe&str=foo&flag&many=1&many=2')

def test_GetOne():
    assert qs.get_one('int').as_name() == '1'
    assert qs.get_one('hex').as_name() == 'babe'
    assert qs.get_one('str').as_name() == 'foo'
    assertRaises(error.web.InputError, qs.get_one, 'flag')
    assertRaises(error.web.InputError, qs.get_one, 'many')

def test_GetMany():
    assert len(qs.get_many('int')) == 1
    assert len(qs.get_many('hex')) == 1
    assert len(qs.get_many('str')) == 1
    assert len(qs.get_many('flag')) == 0
    assert len(qs.get_many('many')) == 2

def test_HasKey():
    assert qs.has_key('int') == 1
    assert qs.has_key('hex') == 1
    assert qs.has_key('str') == 1
    assert qs.has_key('flag') == 1
    assert qs.has_key('many') == 1
    assert qs.has_key('1') == 0
    assert qs.has_key('foo') == 0
    assert qs.has_key('babe') == 0
    assert qs.has_key('other') == 0

def test_WildQuerystrings():
    """Test HTTPQueryString against a sample of query-strings seen
    in the wild."""
    querystring.HTTPQueryString("&foo=bar")
    querystring.HTTPQueryString("foo=bar&")
    querystring.HTTPQueryString("foo=bar&&")
    assertRaises(querystring.QueryStringError, querystring.HTTPQueryString, '=bar')

def test_Q():
    q = querystring.HTTPQueryString('q=%25geek%25')
    assert q.get_one('q').as_unixstr() == '%geek%'

#class UnvalidatedInputTestCase(unittest.TestCase):
int = querystring.UnvalidatedInput('a', '1')
hex = querystring.UnvalidatedInput('b', 'babe')
str = querystring.UnvalidatedInput('c', 'foo')

def test_Integer():
    assert int.as_int() == 1
    assert hex.as_int(16) == 0xBABE
    assert hex.as_name() == 'babe'
    assertRaises(error.web.InputError, str.as_int)
