from .base import MnLLibrary
from .base import PyMnLFunction

class FileIO(MnLLibrary):
    def __init__(self):
        self.namespace = {
            'open': PyMnLFunction('open', open)
        }
        self.initialized = True
        self.need_cleanup = False