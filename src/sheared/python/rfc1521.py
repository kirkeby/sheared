def parse_content_type(ct):
    pieces = ct.split(';')
    
    ct = pieces[0].strip()
    if not ct:
        raise ValueError, 'empty content-type'
    type, subtype = ct.split('/')
    if not type.strip() and subtype.split():
        raise ValueError, 'type or subtype missing in content-type'

    params = {}
    for param in pieces[1:]:
        k, v = param.split('=', 1)
        params[k] = v

    return ct, params
