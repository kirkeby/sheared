# vim:textwidth=0:nowrap
from __future__ import generators
import __builtin__

import re

def lex_tales_string(text):
    """lex_tales_string(text) -> [text, path, ...]"""
    list = []

    s = ''
    while text:
        i = text.find('$')
        if i < 0:
            s = s + text
            text = ''

        elif text[i:i+2] == '$$':
            s = s + text[:i+1]
            text = text[i+2:]

        else:
            s = s + text[:i]
            text = text[i+1:]
            if text[0:1] == '{':
                j = text.index('}')
                v = text[1:j]
                text = text[j+1:]
            else:
                try:
                    v, text = text.split(maxsplit=1)
                except:
                    v, text = text, ''

            list.append(s)
            list.append(compile(v))
            s = ''

    if s:
        list.append(s)
    return list

re_type_prefixed = re.compile('^\s*(\S+):\s*(.*)$')
def compile(text):
    """compile(text) -> tales-program

    Compile a Template Attribute Language Expression Syntax (version 1.2)
    expression.
    """
    try:
        (prefix, expression), = re_type_prefixed.findall(text)
    except ValueError:
        prefix, expression = 'path', text

    if prefix == 'not':
        return 'not', compile(expression)

    if prefix == 'path':
        return 'path', expression.split('/')

    if prefix == 'string':
        return 'string',  lex_tales_string(expression)

    if prefix == 'python':
        code = __builtin__.compile(expression, '[no file]', 'eval')
        return 'python', code

    raise 'unknown prefix in TALES expression'

def walkPath(context, path):
    for step in path:
        try:
            context = context[step]
            continue
        except KeyError:
            pass
        try:
            context = getattr(context, step)
            continue
        except AttributeError:
            raise KeyError, 'cannot find "%s" on %r' % (step, context)
    return context

def execute((op, arg), context):
    if op == 'not':
        return not execute(arg, context)
    if op == 'path':
        return walkPath(context, arg)
    if op == 'string':
        s = ''
        for i in range(len(arg)):
            if i % 2:
                s = s + str(execute(arg[i], context))
            else:
                s = s + arg[i]
        return s
    if op == 'python':
        return eval(arg, {})

    raise 'unknown op-code'
