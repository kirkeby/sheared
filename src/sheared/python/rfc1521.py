from pyros import ox
from pyros import lex
from pyros.lex import LexicalError
from pyros.lex.token import Token, EOF, Atom, String

class SemiColon(Token):
    pass
class Equal(Token):
    pass
class ParameterListLexer(lex.Lexer):
    def __init__(self):
        lex.Lexer.__init__(self)
        self.addPattern(r'[a-zA-Z0-9_.-]+', Atom)
        self.addPattern(r'"[^"]*"', String)
        self.addPattern(r';', SemiColon)
        self.addPattern(r'=', Equal)
plist_lexer = ParameterListLexer()

def parse_plist_header(hdr):
    all = hdr.split(';', 1)
    header, parameters = all[0], {}
    header = header.strip()
    if not header:
        raise ValueError, 'no content-type'
    
    if len(all) > 1:
        tokens = list(plist_lexer.lex(';'+all[1]))
        while len(tokens) > 1:
            m = ox.match([SemiColon, Atom, Equal], tokens)
            if not m:
                raise ValueError, 'no match for %r' % tokens
            tokens = tokens[3:]
            name = m[1].lexeme

            if tokens:
                m = ox.match([Atom], tokens)
                if m:
                    value = m[0].lexeme
                else:
                    m = ox.match([String], tokens)
                    if not m:
                        raise ValueError, 'no match for %r' % tokens
                    value = m[0].lexeme[1:-1]
                tokens = tokens[1:]
            else:
                value = ''

            parameters[name] = value

    return header, parameters

def parse_content_type(ct):
    content_type, params = parse_plist_header(ct)

    t, st = content_type.split('/')
    if not t and st:
        raise ValueError, 'type and/or subtype missing'
    
    return content_type, params
