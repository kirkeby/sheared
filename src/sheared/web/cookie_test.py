from sheared.web import cookie

def test_Simple():
    cake = cookie.Cookie('name', 'foo@bar.com')
    baked = cookie.parse(cookie.format(cake))
    
    assert cake.name == baked.name
    assert cake.value == baked.value
