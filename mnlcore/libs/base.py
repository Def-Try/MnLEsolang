class MnLLibrary:
    def __init__(self):
        self.namespace = {}
        self.initialized = True
        self.need_cleanup()

    def init(self): pass
    def cleanup(self): pass

class PyMnLFunction():
    def __init__(self, name, function):
        self.name = name
        self.func = function

    def __call__(self, *args):
        return self.func(*args)