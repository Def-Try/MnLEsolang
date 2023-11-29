from .base import MnLLibrary
from .base import PyMnLFunction

def _fout(*values, sep=" ", end="\n", flush=True):
    print(values)
    self.stdout += sep.join([str(v) for v in values])+end
def _fin(_):
    if inp == "":
        return ""
    inp = self.stdin[:self.stdin.index("\n")]
    self.stdin = self.stdin[(self.stdin.index("\n")+1):]
    return inp

class FakeIO(MnLLibrary):
    def __init__(self):
        self.stdout = ""
        self.stdin = ""
        self.namespace = {
            'input': PyMnLFunction('input', _fin),
            'print': PyMnLFunction('print', _fout)
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
