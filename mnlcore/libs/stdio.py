from .base import MnLLibrary
from .base import PyMnLFunction

class STDIO(MnLLibrary):
    def __init__(self):
        self.namespace = {
            'print': PyMnLFunction('print', print),
            'input': PyMnLFunction('input', input)
        }
        self.initialized = True
        self.need_cleanup = False