"""The Irregular Expression Language

<dl>
<dt>&lt;foo&gt; &lt;bar&gt; &lt;baz&gt;</dt>
<dd>A tag foo, containing a tag bar, containing a tag baz; e.g.:
<pre>&lt;foo&gt;
    Hello, World!
    &lt;bar&gt;
        &lt;baz /&gt;
    &lt;/bar&gt;
    &lt;/foo&gt;
</pre>
</dd>

BEWARE: The following is _not_ yet implemented.

<dt>&lt;foo&gt;, &lt;bar&gt;, &lt;baz&gt;</dt>
<dd>A tag foo, followed by a tag bar, followed by tag baz; e.g.:
<pre>&lt;foo&gt;&lt;/foo&gt;
    &lt;bar /&gt;
    &lt;baz&gt;Hello, World!&lt;/baz&gt;
</pre>
</dd>
</dl>
"""

# Step 1: Generate a parse-tree of the XML document.
# Step 2: Match the ireg against the generated tree.
# Step 3: ?!
# Step 4: Profit!

from __future__ import generators

import abml

#def match(program, tree):
#    if not program:
#        return 1
#
#    if tree.type == 'start-tag' and program[0] == tree.name:
#        program = program[1:]
#
#    for child in tree.children:
#        if match(program, child):
#            return 1
#
#    return not program

def treeify(xml):
    """treeify(str) -> xml-parse-tree

    Generates a parse tree for the XML-document, str.  Each subtree in
    the parse tree is an abml.Element instance with a children attribute
    grafted onto."""

    class Tree:
        def __init__(self):
            self.type = None
            self.children = []
    stack = [Tree()]

    for ev in abml.parse(xml):
        stack[-1].children.append(ev)
        ev.children = []
        if ev.type == 'start-tag':
            stack.append(ev)
        elif ev.type == 'end-tag':
            stack.pop().children.pop()

    assert len(stack) == 1
    return stack[0]

def compile(ir):
    """compile(str) -> compiled-ir-fragment"""

    fragments = []

    for fragment in ir.split():
        fragment = fragment.strip()
        if not fragment:
            continue

        if fragment[0] == '(' and fragment[-1] == ')':
            fragment = fragment[1:-1]
            capture = 1
        else:
            capture = 0

        if not fragment[0] == '<' and fragment[-1] == '>':
            raise 'malformed XML-fragment: %r' % fragment

        fragments.append((capture, fragment[1:-1]))

    return fragments

def match(program, tree):
    if not program:
        return 1

    if tree.type == 'start-tag' and program[0][1] == tree.name:
        program = program[1:]

    for child in tree.children:
        if match(program, child):
            return 1

    return not program

def find(fragments, subtree, captured=()):
    if subtree.type == 'start-tag' and fragments[0][1] == subtree.name:
        if fragments[0][0]:
            captured = captured + (subtree,)
        fragments = fragments[1:]

    if fragments:
        for child in subtree.children:
            for found in find(fragments, child, captured):
                yield found
    else:
        yield captured

if __name__ == '__main__':
    from pprint import pprint
    def ptree(root, level=0):
        print '  ' * level, `root`
        for child in root.children:
            ptree(child, level+1)
    
    xml = '<xml><foo>Hello, World!</foo>' \
               '<foo>The Answer is . . . . . .  42</foo>' \
               '<bar />' \
          '</xml>'

    tree = treeify(xml)

    assert match(compile(''), tree)
    assert match(compile('<xml>'), tree)
    assert match(compile('<foo>'), tree)
    assert match(compile('<bar>'), tree)
    assert match(compile('<xml> <foo>'), tree)
    assert match(compile('<xml> <bar>'), tree)
    
    assert not match(compile('<foo> <xml> <bar>'), tree)
    assert not match(compile('<foo> <bar> <xml>'), tree)
    assert not match(compile('<bar> <foo>'), tree)
    assert not match(compile('<foo> <bar>'), tree)
    assert not match(compile('<foo> <foo>'), tree)
    assert not match(compile('<baz>'), tree)
    assert not match(compile('<foo> <baz>'), tree)

    for foo, in find(compile('<xml> (<foo>)'), tree):
        print `foo.children`

    print 'All tests passed.'

__all__ = ['compile', 'match', 'treeify']
