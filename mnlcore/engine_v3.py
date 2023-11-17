import textwrap
from . import engine_v3_core

version = "3.0"
from . import exceptions


class MnLEngine():
    def __init__(self):
        core = engine_v3_core

    def reinit(self):
        return self.__init__()

    def load_module(self, module):
        pass

    def run(self, code):
        try:
            self.core.run("<stdin>", code)
        except engine_v3_core.IllegalCharError as e:
            raise exceptions.MnLParserError(f"{e.error_name}: {e.details}", "<none>")
        except engine_v3_core.ExpectedCharError as e:
            raise exceptions.MnLParserError(f"{e.error_name}: {e.details}", "<none>")
        except engine_v3_core.InvalidSyntaxError as e:
            raise exceptions.MnLParserError(f"{e.error_name}: {e.details}", "<none>")
        except engine_v3_core.RTError as e:
            raise exceptions.MnLExecutorError(f"{e.error_name}: {e.details}\n{e.generate_traceback()}", "<none>", -1, e)

    def __str__(self=None):
        return "MnLEngine_v3"
