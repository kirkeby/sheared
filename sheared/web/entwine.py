import warnings

from dtml import tal, metal, tales, context

from sheared.python import io

class Entwiner:
    def __init__(self):
        self.builtins = context.BuiltIns({})
        #self.context = context.Context()
        #self.context.setDefaults(self.builtins)

    def handle(self, request, reply, subpath):
        self.context = {}
        self.entwine(request, reply, subpath)
        r = self.execute(self.page_path, throwaway=0)

        reply.send(r)

    def execute(self, path, throwaway=1):
        r = io.readfile(path)
        c = tal.compile(r, tales)
        r = tal.execute(c, self.context, self.builtins, tales)
        c = metal.compile(r, tales)
        r = metal.execute(c, self.context, self.builtins, tales)

        if throwaway and r.strip():
            warnings.warn('%s: ignored non-macro content' % path)

        return r
