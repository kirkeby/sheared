import warnings

from dtml import tal, metal, tales, context

from sheared.python import io

class Entwiner:
    def __init__(self):
        self.builtins = context.BuiltIns({})
        self.context = context.Context()
        self.context.setDefaults(self.builtins)

    def handle(self, request, reply, subpath):
        self.context.pushContext()
    
        self.entwine(request, reply, subpath)

        r = io.readfile('templates/page.html')
        c = tal.compile(r, tales.compile)
        r = tal.execute(c, self.context, self.builtins, tales.execute)
        c = metal.compile(r, tales.compile)
        r = metal.execute(c, self.context, self.builtins, tales.execute)

        self.context.popContext()

        reply.send(r)

    def execute(self, path):
        r = io.readfile(path)
        c = tal.compile(r, tales.compile)
        r = tal.execute(c, self.context, self.builtins, tales.execute)
        c = metal.compile(r, tales.compile)
        r = metal.execute(c, self.context, self.builtins, tales.execute)
        if r.strip():
            warnings.warn('%s: ignored non-macro content' % path)
