from __future__ import generators

import string

#     FIXME 
# the lexer does not do proper lexing of attributes, and it fails to
# remove backslashes infront of escaped characters.

class LexicalError(Exception):
    pass

class ParserError(Exception):
    pass

def lex(text):
    """This is a lexer for a simple angle-bracketed markup language,
    that looks like this:

      <markup>text</markup>
      <markup />
      <markup things separated by whitespace />

    That is all there is to it.  Really.  Anything goes, escape things
    with backslashes."""

    while text:
        # find beginning of next tag,
        i = text.find('<')
        if i < 0:
            yield 'text', text
            break
        elif i > 0:
            yield 'text', text[:i]

        # search for end of tag, all the while white-space separating
        # the attributes
        words = []
        quotes = None
        escaped = 0
        # j is the last piece of whitespace encountered, k is where we
        # are in the lexing currently
        j = i
        for k in range(j, len(text)):
            if escaped:
                escaped = 0
                continue
            if text[k] == '\\':
                escaped = 1
                continue
            if quotes:
                if text[k] == quotes:
                    quotes = None
                continue
                
            if text[k] == '>':
                if k > j + 1:
                    words.append(text[j+1:k])
                break

            if text[k] in '\"\'':
                quotes = text[k]
            if text[k] in string.whitespace:
                words.append(text[j+1:k])
                j = k
        else:
            raise LexicalError, 'never-ending tag spotted'

        yield 'tag', (words, text[i:k+1])

        text = text[k+1:]

def parse_attribute(str):
    try:
        name, value = str.split('=', 1)
        # Yes, we do the lexers work here and it is ugly, but it is easy
        # and it works.
        if len(value) > 0 and value[0] in "\'\"":
            assert value[-1] == value[0], 'Lexer handed me crap for attribute'
            value = value[1:-1]
    except ValueError:
        name, value = str, None
    try:
        ns, name = name.split(':', 1)
    except:
        ns = None
    return ns, name, value

class Element:
    def __init__(self, type, **kwargs):
        self.type = type
        self.__dict__.update(kwargs)

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
            yield Element('text', raw=value)
            
        elif what == 'tag':
            value, raw = value[0], value[1]
            if value[0][0] == '!':
                # this is a doctype-lookalike
                value[0] = value[0][1:]
                attr = map(parse_attribute, value[1:])
                yield Element('doctype', name=value[0], attributes=attr, raw=raw)
                
            elif value[0][0] == '?' and value[-1][-1] == value[0][0]:
                # this is a processing instruction
                value[0] = value[0][1:]
                value[-1] = value[-1][:-1]
                attr = map(parse_attribute, value[1:])
                yield Element('processing-instruction', name=value[0], attributes=attr, raw=raw)
                
            elif value[0][0] == '/':
                # this is an end-tag
                if len(value) > 1:
                    raise ParserError, 'end-tag with attributes'
                if not value[0][1:] == stack[-1]:
                    raise ParserError, 'overlapping nested tags'
                tag = stack.pop()
                yield Element('end-tag', name=value[0][1:], raw=raw)
                
            else:
                # this is a start-tag ...
                attr = []
                for a in map(parse_attribute, value[1:]):
                    if a[1]:
                        attr.append(a)

                if len(attr) > 0 and attr[-1][1] == '/':
                    attr = attr[:-1]
                    suicidal = 1
                else:
                    suicidal = 0

                yield Element('start-tag', name=value[0], attributes=attr, raw=raw)
                if suicidal:
                    # ... which ends itself
                    yield Element('end-tag', name=value[0], raw='')
                else:
                    # ... or not
                    stack.append(value[0])
    
        else:
            raise InternalError, 'unknown thing %r from lexer' % what

    if stack:
        raise ParserError, 'open tags after end-of-document'

if __name__ == '__main__':
    xml = '''<!doctype foo><?xml fisk?><baz><tag name="value \\"\\'\\\\" />text</baz>'''
    for event in parse(xml):
        print `event`
