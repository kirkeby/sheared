# vim:textwidth=0:nowrap
from __future__ import generators

import abml

from tal import format_tag

class SyntaxError(Exception):
    pass

def compile(text, exp):
    """compile(text) -> [METAL instructions]
    
    This is a compiler for the Macro Expansion Template Attribute
    Language version 1.0. For more information see,
    
      http://www.zope.org/Wikis/DevSite/Projects/ZPT/METAL%20Specification%201.0

    Differences from METAL 1.0:

    - the METAL builtins define-slot and fill-slot are not implemented.

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
            context[-1].append(('structure', element.raw))
        elif element.type == 'doctype':
            context[-1].append(('structure', element.raw))
        elif element.type == 'processing-instruction':
            context[-1].append(('structure', element.raw))

        elif element.type == 'start-tag':
            metal_attr = {}
            other_attr = []

            for ns, name, value in element.attributes:
                if ns == 'metal':
                    metal_attr[name] = value
                else:
                    other_attr.append((ns, name, value))

            if metal_attr:
                if metal_attr.has_key('define-macro') and metal_attr.has_key('use-macro'):
                    raise SyntaxError, 'do not know how to define and use macros at the same time'
                has_ctx.append(1)
                context.append([])

                start = format_tag(element.name, other_attr)
                end = '</%s>' % element.name
                context[-1].append(('start-tag', element.name, start, end, metal_attr))

            else:
                has_ctx.append(0)
                context[-1].append(('structure', element.raw))

        elif element.type == 'end-tag':
            if has_ctx.pop():
                thing = context.pop()

                tag = thing.pop(0)
                tag, start, end, metal_attr = tag[:2], tag[2], tag[3], tag[4]

                thing.insert(0, ('structure', start))
                thing.append(('structure', end))

                assert tag[0] == 'start-tag', 'internal compiler error'
                assert tag[1] == element.name, 'internal compiler error'

                if metal_attr.has_key('define-macro'):
                    context[-1].append(['define-macro',
                                metal_attr['define-macro'], thing])
                elif metal_attr.has_key('use-macro'):
                    context[-1].append(['use-macro',
                                exp.compile(metal_attr['use-macro']), thing])

            else:
                context[-1].append(('structure', element.raw))

    assert len(context) == 1, 'internal compiler error: %r' % context
    return context[0]

def execute(program, context, builtins, exp):
    result = ''
    for instruction in program:
        op = instruction[0]
        if op == 'structure':
            result += instruction[1]

        elif op == 'define-macro':
            name, macro = instruction[1], instruction[2]
            context[name] = macro

        elif op == 'use-macro':
            expr, block = instruction[1], instruction[2]
            try:
                block = exp.execute(expr, context)
            except:
                pass
            result += execute(block, context, builtins, exp)

        else:
            raise 'unknown op-code in %s' % `instruction`

    return result
