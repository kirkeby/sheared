#
# Sheared -- non-blocking network programming library for Python
# Copyright (C) 2003  Sune Kirkeby <sune@mel.interspace.dk>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
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

def treeify(events):
    """treeify(str) -> xml-parse-tree

    Generates a parse tree for the XML-document, str.  Each subtree in
    the parse tree is an abml.Element instance with a children attribute
    grafted onto."""

    class Tree:
        def __init__(self):
            self.type = None
            self.children = []
    stack = [Tree()]

    for ev in events:
        stack[-1].children.append(ev)
        ev.children = []
        if ev.type == 'start-tag':
            stack.append(ev)
        elif ev.type == 'end-tag':
            stack.pop().children.pop()

    assert len(stack) == 1
    return stack[0]

class TagName:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return self.name == other[1]

class Fragment:
    def __init__(self, capture, **kwargs):
        self.capture = capture
        self.fields = kwargs

    def matches(self, subtree):
        for k, v in self.fields.items():
            if not hasattr(subtree, k):
                return 0
            if not v == getattr(subtree, k):
                return 0
        return 1

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

        if fragment[0] == '<' and fragment[-1] == '>':
            fragments.append(Fragment(capture, type='start-tag',
                        name=TagName(fragment[1:-1])))

        elif fragment == 'text':
            fragments.append(Fragment(capture, type='text'))

        else:
            raise 'malformed IR-fragment: %r' % fragment

    return fragments

def match(program, tree):
    if not program:
        return 1

    if program[0].matches(tree):
        program = program[1:]

    for child in tree.children:
        if match(program, child):
            return 1

    return not program

def find(fragments, subtree, captured=()):
    fragment = fragments[0]
    if fragment.matches(subtree):
        if fragment.capture:
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

    import abml
    tree = treeify(abml.parse(xml))

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

    # FIXME -- turn into an assert
    #for foo, in find(compile('<xml> <foo> (text)'), tree):
    #    print `foo.raw`

    print 'All tests passed.'

__all__ = ['compile', 'match', 'treeify']
