from .base import MnLLibrary
from .base import PyMnLFunction

class FakeIO(MnLLibrary):
    def _fout(self, *values, sep=" ", end="\n", flush=True):
        self.stdout += sep.join([str(v) for v in values])+end
    def _fin(self, _):
        if inp == "":
            return ""
        inp = self.stdin[:self.stdin.index("\n")]
        self.stdin = self.stdin[(self.stdin.index("\n")+1):]
        return inp

    def __init__(self):
        self.stdout = ""
        self.stdin = ""
        self.namespace = {
            'input': PyMnLFunction('input', self._fin),
            'print': PyMnLFunction('print', self._fout)
        }
        self.initialized = False
        self.need_cleanup = False
    def read_output(self, amount=0):
        if not amount or amount == -1 or amount == 0:
            out = self.stdout
            self.stdout = ""
            return out
        out = self.stdout[:amount]
        self.stdout = self.stdout[amount:]
        return out
    def send_input(self, inp, end="\n"):
        self.stdin += inp+end

    def init(self):
        self.initialized = True
        return self
