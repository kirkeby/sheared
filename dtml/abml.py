from __future__ import generators

import string

#     FIXME 
# the lexer does not do proper lexing of attributes, and it fails to
# remove backslashes infront of escaped characters.

class LexicalError(Exception):
    pass

class ParseError(Exception):
    pass

def lex_outer(text):
    """This is the lexer for the "outer part" of the simple
    angle-bracketed markup language described in lex. It lexes
    the tags and text, but not the tag-attributes."""

    while text:
        # find beginning of next tag,
        i = text.find('<')

        if i < 0:
            # no more tags, done
            yield 'text', text
            break
        elif i > 0:
            # there is text between here and next tag
            yield 'text', text[:i]
        text = text[i:]

        # search for end of tag
        quotes = None
        escaped = 0
        for j in range(len(text)):
            if escaped:
                escaped = 0
                continue
            if text[j] == '\\':
                escaped = 1
                continue
            if quotes:
                if text[j] == quotes:
                    quotes = None
                continue
            if text[j] == '>':
                break
            if text[j] in '\"\'':
                quotes = text[j]

        else:
            raise LexicalError, 'never-ending tag spotted'

        yield 'tag', text[1:j]
        text = text[j+1:]

#try:
#    import cabml
#    lex_outer = cabml.lex_outer
#except:
#    raise
#    pass

def lex_inner(tag):
    # split tag into name and attributes
    try:
        name, attr = tag.strip().split(None, 1)
    except ValueError:
        name, attr = tag.strip(), ''

    if not name:
        raise LexerError, 'no name in tag'

    # special cases for </tag> and <tag/>, <!doctype> and
    # <?processing-instructions?>
    if name[0] == '!':
        name = name[1:]
        yield 'doctype', (name, '<%s>' % tag, lex_attributes(attr))

    elif name[0] == '?' and attr[-1] == '?':
        name = name[1:]
        attr = attr[:-1]
        yield 'processing-instruction', (name, '<%s>' % tag, lex_attributes(attr))
        
    elif name[0] == '/':
        name = name[1:]
        if attr:
            raise LexerError, 'end-tag cannot have attributes'
        yield 'end-tag', (name, '<%s>' % tag)

    elif attr and attr[-1] == '/':
        attr = attr[:-1]
        yield 'start-tag', (name, '<%s>' % tag, lex_attributes(attr))
        yield 'end-tag', (name, '')

    else:
        yield 'start-tag', (name, '<%s>' % tag, lex_attributes(attr))

def lex_attributes(str):
    attrs = []

    j = 0
    escaped = 0
    quotes = None
    for i in range(len(str)):
        if quotes:
            if escaped:
                escaped = 0
                continue
            if str[i] == '\\':
                escaped = 1
                continue
            if str[i] == quotes:
                quotes = None
                yield 'string', str[j:i]
                j = i + 1
            continue

        if str[i] in '\'\"':
            if str[j:i].strip():
                yield 'bare-word', str[j:i]
            j = i + 1
            quotes = str[i]

        if str[i] == '=':
            if str[j:i].strip():
                yield 'bare-word', str[j:i]
            yield 'equal', None
            j = i + 1

        if str[i] == ':':
            if str[j:i].strip():
                yield 'bare-word', str[j:i]
            yield 'colon', None
            j = i + 1

        if str[i] in string.whitespace:
            if str[j:i].strip():
                yield 'bare-word', str[j:i]
            j = i + 1

    if escaped:
        raise LexerError, 'escape past end of string'
    if quotes:
        raise LexerError, 'quotes past end of string'

    if str[j:].strip():
        yield 'bare-word', str[j:]
        
def lex(text):
    """This is a lexer for a simple angle-bracketed markup language,
    that looks like this:

      <markup>text</markup>
      <markup />
      <markup things separated by whitespace />

    That is all there is to it.  Really.  Anything goes, escape things
    with backslashes."""

    for e, a in lex_outer(text):
        if e == 'text':
            yield e, a
        elif e == 'tag':
            for e, a in lex_inner(a):
                yield e, a
        else:
            raise InternalError, 'unknown event from lex_outer'

def parse_name(name):
    try:
        namespace, name = name.split(':', 1)
    except:
        namespace, name = None, name
    return namespace, name

def parse_attributes(attr):
    attributes = []

    attr = list(attr)

    while attr:
        if not attr[0][0] == 'bare-word':
            raise ParseError, ('expecting bare-word found %s' % attr[0][0], attr)
        name = attr.pop(0)[1]

        if len(attr):
            if attr[0][0] == 'colon':
                attr.pop(0)
                if not attr[0][0] == 'bare-word':
                    raise ParseError, ('expecting bare-word after colon found %s' % attr[0][0], attr)
                namespace = name
                name = attr.pop(0)[1]
            else:
                namespace = None

            if attr[0][0] == 'equal':
                attr.pop(0)
                if not attr[0][0] == 'string':
                    raise ParseError, ('expecting string after equal found %s' % attr[0][0], attr)
                value = attr.pop(0)[1]
            else:
                value = None

        else:
            namespace, value = None, None

        attribute = namespace, name, value
        attributes.append(attribute)

    return attributes

class Element:
    def __init__(self, type, **kwargs):
        self.type = type
        self.__kwargs = kwargs
        self.__dict__.update(kwargs)
    def __repr__(self):
        return str(self)
    def __str__(self):
        return 'Element(%s, %r)' % (self.type, self.__kwargs)

def parse(text):
    """This is a simple parser for a simple angle-bracketed markup
    language. It enforces the following,

     - tags may not overlap
     - all tags must be closed, either like <thus />'ly, or
       with a real </close>-tag

    except for XML-like doctype and processing-instruction tags,
    which are those that begin and end with resp. an exclamation-mark
    and a question-mark."""

    stack = []
    for event in lex(text):
        what, value = event
        
        if what == 'text':
            yield Element(what, raw=value)

        elif what in ('doctype', 'processing-instruction', 'start-tag'):
            name, raw, attr = value
            if what == 'start-tag':
                name = parse_name(name)
                attr = list(attr)
                attr = parse_attributes(attr)
            else:
                attr = list(attr)
            yield Element(what, name=name, attributes=attr, raw=raw)

            if what == 'start-tag':
                stack.append(name)

        elif what == 'end-tag':
            name, raw = value
            name = parse_name(name)
            other = stack.pop()
            if not other == name:
                raise ParseError, 'overlapping nested tags: %s vs %s' % (name, other)
            yield Element(what, name=name, raw=raw)
            
        else:
            raise InternalError, 'unknown thing %r from lexer' % what
 
    if stack:
        raise ParseError, 'open tags after end-of-document'

if __name__ == '__main__':
    xml = '''<!doctype foo><?xml fisk?><baz><tag name="value \\"\\'\\\\" />text</baz>'''
    for event in parse(xml):
        print `event`
