# vim:textwidth=0:nowrap
from __future__ import generators

import re, sys, types

import abml

class SyntaxError(Exception):
    pass

def format_attribute(attr):
    if len(attr) == 2:
        ns, (name, value) = None, attr
    elif len(attr) == 3:
        ns, name, value = attr
    else:
        raise 'bad attribute-tuple: %s' % `attr`
    s = ''
    if not ns is None:
        s += '%s:' % ns
    s += name
    if not value is None:
        s += "=%r" % value
    return s

def format_tag(name, attributes):
    words = [name]
    words.extend(map(format_attribute, attributes))
    return '<%s>' % ' '.join(words)

def split_list(text, needle=';'):
    """split_list(text) -> [list of strings]
    
    Split a string into a list of strings at each semi-colon in the
    string, except where the semi-colon is escaped by a semi-colon."""
    i = 0
    j = text.find(needle)
    while j > 0:
        if j < len(text) - 1 and text[j+1] == needle:
            j = j + 1
        else:
            yield text[i:j]
            i = j + 1
        j = text.find(needle, j + 1)
    yield text[i:]

re_define = re.compile('^\s*(local\s+|global\s+)?(\S+)\s(.+)$')
def parse_define(text):
    """parse_define(text) -> (scope, name, expression)
    
    Parse text as a single define_scope EBNF non-terminal.
    """
    (scope, name, expression), = re_define.findall(text)
    if scope == '':
        scope = 'local'
    return scope, name, expression

re_attribute = re.compile('^\s*(\S+)\s(.+)$')
def parse_attribute(text):
    """parse_attribute(text) -> (name, expression)

    Parse text as an attribute_statement EBNF non-terminal.
    """
    (name, expression), = re_attribute.findall(text)
    return name, expression

re_replace = re.compile('^\s*(text\s|structure\s)?(.+)*$')
def parse_replace_expression(text):
    """parse_replace_expression(text) -> ('text' | 'structure', expression)

    Parse text as an EBNF argument non-terminal for the text-replacing
    TAL attributes (replace, content and on-error).
    """
    (type, expression), = re_replace.findall(text)
    type = type.strip()
    if type == '':
        type = 'text'
    return type, expression

re_repeat = re.compile('^\s*(\S+)\s(.+)$')
def parse_repeat(text):
    """parse_repeat(text) -> (name, expression)

    Parse text as an EBNF argument non-terminal for the repeat TAL
    attribute.
    """
    (name, expression), = re_repeat.findall(text)
    return name, expression

def compile(text, exp):
    """compile(text) -> [TAL instructions]
    
    This is a compiler for the Template Attribute Language version
    1.4. For more information see,
    
      http://dev.zope.org/Wikis/DevSite/Projects/ZPT/TAL%20Specification%201.4

    Differences from TAL 1.4:

    - the TALES builtin attrs is not implemented.

    - the TALES builtin repeat is not implemented.

    - this library is a extremely lenient in what it lets you get away with
      in tag names, attribute names and expression names, and also it
      does not care if you properly xmlns:tal="..." your blocks of TAL-code.
      Abuse these properties at your own peril.
    """

    has_ctx = []
    context = []
    context.append([])

    for element in abml.parse(text):
        if element.type == 'text':
            context[-1].append(('static', element.raw))
        elif element.type == 'doctype':
            context[-1].append(('static', element.raw))
        elif element.type == 'processing-instruction':
            context[-1].append(('static', element.raw))

        elif element.type == 'start-tag':
            tal_attr = {}
            other_attr = []

            for ns, name, value in element.attributes:
                if ns == 'tal':
                    tal_attr[name] = value
                else:
                    other_attr.append((ns, name, value))

            if tal_attr:
                if tal_attr.has_key('content') and tal_attr.has_key('replace'):
                    raise SyntaxError, 'cannot have both tal:content and tal:replace on same tag'

                has_ctx.append(1)
                context.append([])
                context[-1].append(('start-tag', element.name, other_attr, tal_attr))

            else:
                has_ctx.append(0)
                context[-1].append(('static', element.raw))

        elif element.type == 'end-tag':
            if has_ctx.pop():
                thing = context.pop()

                tag = thing.pop(0)
                tag, tal_attr = tag[:3], tag[3]

                assert tag[0] == 'start-tag', 'internal compiler error'
                assert tag[1] == element.name, 'internal compiler error'

                scopes = []
                
                omit_tag = None
                attributes = []
                replace = None
                if tal_attr.get('omit-tag', ''):
                    omit_tag = exp.compile(tal_attr['omit-tag'])
                if tal_attr.get('attributes', ''):
                    attributes = list(split_list(tal_attr['attributes']))
                    attributes = map(parse_attribute, attributes)
                    attributes = [(x[0], exp.compile(x[1])) for x in attributes]
                if tal_attr.get('replace', ''):
                    replace = 'all'
                    replace_ex = tal_attr['replace']
                elif tal_attr.get('content', ''):
                    replace = 'content'
                    replace_ex = tal_attr['content']
                if replace:
                    replacer = parse_replace_expression(replace_ex)
                    replace = replace, replacer[0], exp.compile(replacer[1])

                if not (omit_tag or attributes or replace):
                    scopes.insert(0, ('static-tag', tag[1], tag[2]))
                else:
                    scopes.insert(0, ('dynamic-tag', tag[1], tag[2], attributes, omit_tag, replace))

                if tal_attr.get('repeat', ''):
                    repeater = parse_repeat(tal_attr['repeat'])
                    repeater = repeater[0], exp.compile(repeater[1])
                    scopes.insert(0, ('repeat', repeater))
                if tal_attr.get('condition', ''):
                    condition = exp.compile(tal_attr['condition'])
                    scopes.insert(0, ('condition', condition))
                if tal_attr.get('define', ''):
                    defines = list(split_list(tal_attr['define']))
                    defines = map(parse_define, defines)
                    defines = [(x[0], x[1], exp.compile(x[2])) for x in defines]
                    scopes.insert(0, ('define', defines))
                if tal_attr.get('on-error', ''):
                    replacer = parse_replace_expression(tal_attr['on-error'])
                    replacer = replacer[0], exp.compile(replacer[1])
                    scopes.insert(0, ('on-error', replacer))

                while scopes:
                    scope = scopes.pop()
                    thing = [scope + (thing,)]
                context[-1].extend(thing)

            else:
                context[-1].append(('static', element.raw))

    assert len(context) == 1, 'internal compiler error'
    return optimize_tal(context[0], exp)

def optimize_tal(program, exp):
    if not program:
        return []
    optimized = program

    # recurse into tags that contain blocks
    instruction = optimized[0]
    opcode = instruction[0]
    if opcode in ('static-tag', 'dynamic-tag', 'define', 'replace', 'repeat', 'condition'):
        instruction = instruction[:-1] + \
                      (optimize_tal(instruction[-1], exp),)
    optimized = [instruction] + optimized[1:]

    # optimize tags at head of program
    if opcode == 'static-tag':
        name, attrs, block = optimized[0][1:]
        optimized[0:1] = [('static', format_tag(name, attrs))] + \
                         optimized[0][3] + \
                         [('static', '</%s>' % name)]

    # FIXME -- this would look sooooo much better with pattern-matching :(
    while len(optimized) > 1 and optimized[0][0] == 'static' and optimized[1][0] == 'static':
        optimized[0:2] = [('static', optimized[0][1] + optimized[1][1])]

    # optimize rest of program
    if len(optimized) > 1:
        optimized = [optimized[0]] + optimize_tal(optimized[1:], exp)

    # done!
    return optimized

def execute(program, context, builtins, exp):
    result = ''
    for instruction in program:
        op = instruction[0]
        if op == 'static':
            result += instruction[1]

        elif op == 'structure':
            result += exp.execute(instruction[1], context)

        elif op == 'text':
            s = exp.execute(instruction[1], context)
            if isinstance(s, types.StringTypes):
                s = s.replace('&', '&amp;')
                s = s.replace('<', '&lt;')
                s = s.replace('>', '&gt;')
            elif isinstance(s, types.IntType) or isinstance(s, types.LongType) or isinstance(s, types.FloatType):
                s = str(s)
            else:
                raise ValueError, '%r is not string or number' % s
            result += s

        elif op == 'replace':
            (op, expr), block = instruction[1:]
            result += execute([(op, expr)], context, builtins, exp)

        elif op == 'dynamic-tag':
            name, sta_attrs, dyn_attrs, omit_tag, replace, block = instruction[1:]

            attrs = []
            attrs.extend(sta_attrs)

            if omit_tag:
                omit_tag = exp.execute(omit_tag, context)

            replaced = 0
            if replace:
                scope, with, expr = replace
                content = execute([(with, expr)], context, builtins, exp)
                replaced = 1
                if scope == 'all':
                    omit_tag = 1

            if not replaced:
                content = execute(block, context, builtins, exp)
            
            if not omit_tag:
                for attr in dyn_attrs:
                    for i in range(len(attrs)):
                        # FIXME -- need namespace support
                        if attrs[i][1] == attr[0]:
                            break
                    else:
                        i = len(attrs)
                        attrs.append(())
                    attrs[i] = attr[0], exp.execute(attr[1], context)
                result += format_tag(name, attrs)
            result += content
            if not omit_tag:
                result += '</%s>' % name

        elif op == 'define':
            olv = {}

            for scope, name, exp in instruction[1]:
                val = exp.execute(exp, context)
                if scope == 'local':
                    if context.has_key(name):
                        olv[name] = context[name]
                    context[name] = value
                elif scope == 'global':
                    raise NotImplementedError, 'global scope not implemented'
                else:
                    raise 'unknown scope'

            result += execute(instruction[2], context, builtins, exp)

            for scope, name, exp in instruction[1]:
                if scope == 'local':
                    if olv.has_key(name):
                        context[name] = olv[name]
                    else:
                        del context[name]

        elif op == 'repeat':
            (name, list), block = instruction[1:]
            val = exp.execute(list, context)

            if context.has_key(name):
                has_ov, ov = 1, context[name]
            else:
                has_ov = 0

            # FIXME -- need RepeatVariable class here
            #builtins.pushRepeatVariable(name, elem)
            for elem in val:
                context[name] = elem
                result += execute(block, context, builtins, exp)
            #builtins.popRepeatVariable()

            if has_ov:
                context[name] = ov
            else:
                del context[name]

        elif op == 'condition':
            expr = instruction[1]
            try:
                cond = exp.execute(expr, context)
            except:
                cond = 0
            if cond:
                result += execute(instruction[2], context, builtins, exp)

        else:
            raise 'unknown op-code in %s' % `instruction`

    return result
