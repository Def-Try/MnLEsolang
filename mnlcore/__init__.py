from . import engine_v4
from . import exceptions


class LegacyMnLEngine:
    def __init__(self, *args, **kwargs):
        raise Exception("This MnLEngine was deprecated. Use mnlcore.legacy or mnlcore.engines instead.")

    def __str__(self=None):
        return f"MnLEngine(legacy=True)"

class NonstandardMnLEngine:
    def __init__(self, *args, **kwargs):
        raise Exception("This MnLEngine is nonstandard. Use mnlcore.engines instead.")

    def __str__(self=None):
        return f"MnLEngine(nonstandard=True)"


__VERSION__ = "v2.1"
__ENGINES__ = {
    '1.0': LegacyMnLEngine,
    '2.0': LegacyMnLEngine,
    '3.0': NonstandardMnLEngine,
    '4.0': engine_v4.MnLEngine,

    'default': engine_v4.MnLEngine
}
