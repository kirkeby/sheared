# vim:textwidth=0:nowrap

class Context:
    def __init__(self):
        self.__contexts = [{}]
        self.__defaults = {}
        self.__dictified = None

    def invalidateDictified(self):
        self.__dictified = None

    def setDefaults(self, defaults):
        self.__dictified = None
        self.__defaults = defaults
        self.__defaults.context = self

    def pushContext(self):
        self.__dictified = None
        self.__contexts.append({})
    def popContext(self):
        assert len(self.__contexts) > 1
        self.__dictified = None
        self.__contexts.pop()

    def setGlobal(self, name, value):
        self.__dictified = None
        self.__contexts[0][name] = value
    def setLocal(self, name, value):
        assert len(self.__contexts) > 1
        self.__contexts[-1][name] = value
        if self.__dictified:
            self.__dictified[name] = value

    def has_key(self, name):
        return self.dictify().has_key(name)

    def keys(self):
        return self.dictify().keys()
    def dictify(self):
        if self.__dictified is None:
            self.__dictified = {}
            if self.__defaults:
                self.__dictified.update(self.__defaults.dictify())
            for i in range(len(self.__contexts)):
                self.__dictified.update(self.__contexts[i])
        return self.__dictified

    def __getitem__(self, name):
        for i in range(len(self.__contexts)):
            if self.__contexts[-i-1].has_key(name):
                return self.__contexts[-i-1][name]
        return self.__defaults[name]

    def __delitem__(self, name):
        del self.__contexts[-1][name]
        
#class Default:
#    pass
class BuiltIns:
    def __init__(self, options):
        self.__options = options
        self.__repeat = Context()
        self.__default = None
        self.__attrs = []

    def __getitem__(self, name):
        if name == 'nothing':
            return None
        if name == 'default':
            return self.__default
        if name == 'options':
            return self.__options
        if name == 'repeat':
            return self.__repeat
        if name == 'attrs':
            assert len(self.__attrs) > 0
            return self.__attrs[-1]
        if name == 'CONTEXTS':
            return self
        return self.__repeat[name]

    def keys(self):
        keys = ['nothing', 'default', 'options', 'repeat',
                'CONTEXTS']
        if len(self.__attrs):
            keys.append('attrs')
        keys = keys + self.__repeat.keys()
        return keys
    def dictify(self):
        dict = {}
        for k in self.keys():
            dict[k] = self[k]
        return dict

    def pushRepeatVariable(self, name, value):
        if hasattr(self, 'context'):
            self.context.invalidateDictified()
        self.__repeat.pushContext()
        self.__repeat.setLocal(name, value)
    def popRepeatVariable(self):
        if hasattr(self, 'context'):
            self.context.invalidateDictified()
        self.__repeat.popContext()

    def pushAttrs(self, attrs):
        if hasattr(self, 'context'):
            self.context.invalidateDictified()
        self.__attrs.append(attrs)
    def popAttrs(self):
        if hasattr(self, 'context'):
            self.context.invalidateDictified()
        self.__attrs.pop()
