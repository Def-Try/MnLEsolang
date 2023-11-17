from . import legacy_exceptions as exceptions
from . import legacy_util as util
from . import legacy_modules as modules
try:
    from . import engine_v1
    from . import engine_v2
    print("[W] You are using deprecated legacy MnL Engines. Consider switching to default engine.")
except:
    print("[W] Unable to import .NET-regex based MnL Engines.")
    engine_v1, engine_v2 = None, None

__MODULES__ = modules.__MODULES__

_eval = eval

def eval(*args, **kwargs):
    if "__import__" in args[0]:
        raise exceptions.MnLSecurityError("__import__ usages are restricted from evaluating", args[0])
    if "__builtins__" in args[0]:
        raise exceptions.MnLSecurityError("__builtins__ usages are restricted from evaluating", args[0])
    # if "self" in args[0]:
    #    raise MnLSecurityError("self usages are restricted from evaluating", args[0])
    # print(args)
    return _eval(*args, **kwargs)


legacy_engines = {
    '1.0': engine_v1.MnLEngine,
    '2.0': engine_v2.MnLEngine,
}