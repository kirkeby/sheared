# vim:textwidth=0:nowrap

class Context:
    def __init__(self, defaults={}):
        self.__contexts = [{}]
        self.__defaults = {}

    def setDefaults(self, defaults):
        self.__defaults = defaults

    def pushContext(self):
        self.__contexts.append({})
    def popContext(self):
        assert len(self.__contexts) > 1
        self.__contexts.pop()

    def setGlobal(self, name, value):
        self.__contexts[0][name] = value
    def setLocal(self, name, value):
        assert len(self.__contexts) > 1
        self.__contexts[-1][name] = value

    def __getitem__(self, name):
        for i in range(len(self.__contexts)):
            if self.__contexts[-i-1].has_key(name):
                return self.__contexts[-i-1][name]
        return self.__defaults[name]
        
class Default:
    pass
class BuiltIns:
    def __init__(self, options):
        self.__options = options
        self.__repeat = Context()
        self.__default = Default()
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

    def pushRepeatVariable(self, name, value):
        self.__repeat.pushContext()
        self.__repeat.setLocal(name, value)
    def popRepeatVariable(self):
        self.__repeat.popContext()

    def pushAttrs(self, attrs):
        self.__attrs.append(attrs)
    def popAttrs(self):
        self.__attrs.pop()
