from sheared import reactor
from sheared.python import io
from entwine import abml, ir
from entwine.tree import treeify

import types

def format_param(value, type):
    if type is 'int':
        return '<int>%d</int>' % value
    elif type is 'double':
        return '<double>%f</double>' % value
    elif type is 'string':
        return '<string>%s</string>' % value
    else:
        raise 'unknown param type: %s' % type

def format_request(method, params):
    return """<?xml version='1.0'?>
    <methodCall>
      <methodName>%s</methodName>
      <params>%s</params>
    </methodCall>""" % (method, '\n'.join(map(format_param, params)))

def parse_struct(tree):
    str = {}
    for member in ir.find(ir.compile('(<member>)'), tree):
        assert len(member.children) == 2
        assert member.children[0].name == 'name'
        assert len(member.children[0].children) == 1
        assert member.children[1].name == 'value'
        n = member.children[0].children[0]
        v = parse_value(member.children[1])
        str[n] = v
    return str

def parse_value(tree):
    assert len(tree.children) == 1
    child = tree.children[0]

    if child.type == 'text':
        return child.raw
    elif child.type == 'tag':
        if child.name[1] == 'string':
            return parse_value(child)
        elif child.name[1] == 'int' or child.name == 'i4':
            return int(parse_value(child))
        elif child.name[1] == 'boolean':
            return int(parse_value(child))
        elif child.name[1] == 'double':
            return double(parse_value(child))
        elif child.name[1] == 'struct':
            return parse_struct(child)
        elif child.name[1] == 'array':
            values = ir.find(ir.compile('<data> (<value>)'), child)
            return map(parse_value, [v for v, in values])
        else:
            raise 'unknown value type: %r' % child.name
    else:
        raise 'bad document structure'

def call(host, port, uri, method, params):
    content = format_request(method, params)

    transport = reactor.connectTCP((host, port))
    transport.write('POST %s HTTP/1.0\r\n' % uri)
    transport.write('Host: %s\r\n' % host)
    transport.write('User-Agent: Sheared/XMLRPC\r\n')
    transport.write('Content-Type: text/xml\r\n')
    transport.write('Content-Length: %d\r\n' % len(content))
    transport.write('\r\n')
    transport.write(content)

    reply = transport.read()
    http, content = reply.split('\r\n\r\n')
    status = http.split('\r\n')[0].split()[1]
    if not status == '200':
        raise 'HTTP error: %s' % status

    tree = treeify(abml.strip(abml.parse(content)))
    if ir.match(ir.compile('<methodResponse> <params>'), tree):
        values = list(ir.find(ir.compile('(<value>)'), tree))
        if not len(values) == 1:
            raise 'bad number of <value>s: %d' % len(values)
        return parse_value(values[0][0])
    elif ir.match(ir.compile('<methodResponse> <fault>'), tree):
        raise 'fault'
    else:
        raise 'Unable to parse reply: %r' % tree

def guess_types(args):
    guesses = []
    for arg in args:
        if type(arg) is types.IntType:
            guess = 'int'
        elif type(arg) is types.StringType:
            guess = 'string'
        else:
            raise 'cannot guess XMLRPC type of: %r' % arg
        guesses.append((guess, arg))
    return guesses
class XMLRPCProxy:
    def __init__(self, host, port, uri, prefix=''):
        self.host = host
        self.port = port
        self.uri = uri
        self.prefix = prefix
    
    def __call__(self, *args):
        args = guess_types(args)
        return call(self.host, self.port, self.uri, self.prefix, args)

    def __getattr__(self, key):
        if self.prefix:
            prefix = self.prefix + '.' + key
        else:
            prefix = key
        value = XMLRPCProxy(self.host, self.port, self.uri, prefix)
        setattr(self, key, value)
        return value
