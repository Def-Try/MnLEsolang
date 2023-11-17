import mnlcore

with open('test.mnl', 'r') as tc:
    code = tc.read()

engine = mnlcore.engine_v4.MnLEngine() #  Initialise MnL Engine
# V1 and V2 are based on .NET regex engine, so preferrably do not use them
# V3 was ~~stolen~~ borrowed from some "write your own programming language" guide
#    and adapted to fit engine class methods. Unfortunately, it did not fit syntax
#    of V1 and V2 and was forgotten about for the sake of V4
# V4 is the latest engine that does not use regexes (like V3) AND has syntax from
# V1 and V2. This is the default engine used by mnlcore

# Load V4 standard lib.
# V1 and V2 used "modules", which is basically cool wrapper for dict of methods
# You can still load legacy (v1 and v2) modules with engine.load_module - they
# are going to be automatically converted to library class
fio = engine.load_library(mnlcore.libs.STDIO)
engine.load_syntax_table("")

#try:
engine.run(code)
#except mnlcore.exceptions.BaseError as e:
#    print("[ERROR]", e.message)
#finally:
#    print(fio.read_output())
#    print('Code executed.')
