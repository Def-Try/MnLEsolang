import random
from simpleeval import simple_eval as _eval
from .libs.base import PyMnLFunction
from .libs.base import MnLLibrary

from . import exceptions

version = "4.0"


# from io import StringIO
# import tokenize
# def eval(string, clocals):
#    queue = []
#    for token in tokenize.generate_tokens(StringIO(string).readline):
#    # TODO!

base_syntax_table = '''
IFSTAT -> if
ELSESTAT -> else
EOLT -> ;
DTYPES -> var=/int=int/string=str/float=float/double=float
'''

def index_to_coordinates(s, index, loff):
    """Returns (line_number, col) of `index` in `s`."""
    if not len(s):
        return 1, 1
    sp = s[:index + 1].splitlines(keepends=True)
    return len(sp) + loff, len(sp[-1])

def replace_substrings(s, sb, rw):
    for sbr in sb:
        s = s.replace(sbr, rw)
    return s

class Parser:
    def __init__(self, code, line_offset=0):
        self.code = code
        self.position = -1
        self.values_names = []
        self.line_offset = line_offset
        self.rules = {}
        self.load_syntax_table(base_syntax_table)

    def load_syntax_table(self, syntax_table):
        for rule in syntax_table.split("\n"):
            try:
                self.rules[rule.split("->")[0].strip()] = "->".join(rule.split("->")[1:]).strip()
            except: pass

    def advance(self):
        self.position += 1
        return self.code[self.position]

    def confirm_eolt(self):
        if self.position == len(self.code) - 1:
            self.position -= 1
            raise exceptions.UnexpectedSymbolError(self.advance(),
                                                   index_to_coordinates(self.code, self.position, self.line_offset))
        l = ""
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            l += symbol
            l = l.strip()
            if not self.rules["EOLT"].startswith(l):
                self.position -= 1
                raise exceptions.UnexpectedSymbolError(self.advance(),
                                                       index_to_coordinates(self.code, self.position, self.line_offset))
            if l == self.rules["EOLT"]: break

    def make_value_subtoken(self, eot, dt):
        st = ""
        nc = False
        string = False
        l = ""
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            l += symbol
            if symbol == "\"":
                string = not string
                st += l
                l = ""
                continue
            if string:
                st += l
                l = ""
            if not any([i.startswith(l) or i == l for i in eot]) and not string:
                st += l
                l = ""
            if any([i == l for i in eot]) and not string:
                self.position -= len(l)
                break
            if l == "" and not string and symbol not in "0123456789+-/*^%(). " and not any([i.startswith(l) or i == l for i in self.values_names]):
                self.position -= 1
                raise exceptions.UnexpectedSymbolError(self.advance(),
                                                       index_to_coordinates(self.code, self.position, self.line_offset))
        if nc:
            return 'NC', st.strip()
        try:
            for dtype in self.rules["DTYPES"].split("/"):
                dtype, rdt = dtype.split("=")[0], dtype.split("=")[1]
                if rdt == "": continue
                if dt == dtype:
                    st = eval(f"{rdt}({st})")
        except BaseException:
            raise exceptions.ConversionError(st, dt, index_to_coordinates(self.code, self.position-len(st), self.line_offset))
        return 'R', st
    def make_func_token(self, dt):
        token = ["FUNC", dt, "", [], ""]
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol != " ":
                self.position -= 1
                break
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "(":
                break
            token[2] += symbol
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == " ":
                continue
            self.position -= 1
            break
        while self.position < len(self.code) - 1:
            token[3].append(self.make_value_subtoken([",", ")"], 'var')[1])
            while self.position < len(self.code) - 1:
                symbol = self.advance()
                if symbol == " ":
                    continue
                self.position -= 1
                break
            symbol = self.advance()
            if symbol == ")":
                break
            while self.position < len(self.code) - 1:
                symbol = self.advance()
                if symbol == " ":
                    continue
                self.position -= 1
                break
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "{":
                break
        loff = index_to_coordinates(self.code, self.position + 1, self.line_offset)[0]
        startpositions = [index_to_coordinates(self.code, self.position, self.line_offset)]
        done = 1
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "}":
                done -= 1
            if symbol == "{":
                done += 1
                startpositions.append(index_to_coordinates(self.code, self.position, self.line_offset))
            if done == 0:
                break
            token[4] += symbol
        if done != 0:
            raise exceptions.NotCompleteCodeBlockError(startpositions)
        token[2] = token[2].strip()
        self.values_names.append(token[2])
        parser = Parser(token[4], loff - 1)
        parser.values_names = self.values_names.copy() + token[3]
        token[4] = parser.parse()
        return token

    def make_func_or_value_token(self, dt):
        token = ["SET", "", dt, ""]
        oldpos = self.position
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol != " ":
                self.position -= 1
                break
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == " ":
                break
            token[1] += symbol
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "=":
                break
            if symbol == "(":
                self.position = oldpos
                return self.make_func_token(dt)
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol != " ":
                break
        self.position -= 1
        token[3] = self.make_value_subtoken([self.rules["EOLT"]], dt)
        self.confirm_eolt()
        self.values_names.append(token[1])
        return token

    def make_call_or_value_or_func_token(self, fn):
        token = ["CALL", fn, []]
        oldpos = self.position - len(fn)
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == " ":
                continue
            if symbol == "(":
                break
            if symbol == "=":
                self.position = oldpos
                return self.make_func_or_value_token('var')
            self.position -= 1
            raise exceptions.UnexpectedSymbolError(self.advance(),
                                                   index_to_coordinates(self.code, self.position, self.line_offset))
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == " ":
                continue
            self.position -= 1
            break
        while self.position < len(self.code) - 1:
            token[2].append(self.make_value_subtoken([",", ")"], 'var'))
            while self.position < len(self.code) - 1:
                symbol = self.advance()
                if symbol == " ":
                    continue
                self.position -= 1
                break
            symbol = self.advance()
            if symbol == ")":
                break
            while self.position < len(self.code) - 1:
                symbol = self.advance()
                if symbol == " ":
                    continue
                self.position -= 1
                break
        self.confirm_eolt()
        return token

    def make_if_token(self, ptoken):
        token = ["COND", "IF", "", ""]
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol not in " (":
                self.position -= 1
                raise exceptions.UnexpectedSymbolError(self.advance(),
                                                       index_to_coordinates(self.code, self.position, self.line_offset))
            if symbol == "(":
                break
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == ")":
                break
            token[2] += symbol
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "{":
                break
        loff = index_to_coordinates(self.code, self.position + 1, self.line_offset)[0]
        startpositions = [index_to_coordinates(self.code, self.position, self.line_offset)]
        done = 1
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "}":
                done -= 1
            if symbol == "{":
                done += 1
                startpositions.append(index_to_coordinates(self.code, self.position, self.line_offset))
            if done == 0:
                break
            token[3] += symbol
        if done != 0:
            raise exceptions.NotCompleteCodeBlockError(startpositions)
        parser = Parser(token[3], loff - 1)
        parser.values_names = self.values_names.copy()
        token[3] = parser.parse()
        return token

    def make_elseif_token(self, ptoken):
        if ptoken[0] != "COND" or ptoken[1] not in ("IF"):
            raise exceptions.UnexpectedStatementError("elseif",
                                                      index_to_coordinates(self.code, self.position, self.line_offset))
        token = ["COND", "EIF", "", ""]
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol not in " (":
                self.position -= 1
                raise exceptions.UnexpectedSymbolError(self.advance(),
                                                       index_to_coordinates(self.code, self.position, self.line_offset))
            if symbol == "(":
                break
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == ")":
                break
            token[2] += symbol
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "{":
                break
        loff = index_to_coordinates(self.code, self.position + 1, self.line_offset)[0]
        startpositions = [index_to_coordinates(self.code, self.position, self.line_offset)]
        done = 1
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "}":
                done -= 1
            if symbol == "{":
                done += 1
                startpositions.append(index_to_coordinates(self.code, self.position, self.line_offset))
            if done == 0:
                break
            token[3] += symbol
        if done != 0:
            raise exceptions.NotCompleteCodeBlockError(startpositions)
        parser = Parser(token[3], loff - 1)
        parser.values_names = self.values_names.copy()
        token[3] = parser.parse()
        return token

    def make_else_token(self, ptoken):
        if ptoken[0] != "COND" or ptoken[1] not in ("IF", "EIF"):
            raise exceptions.UnexpectedStatementError("else",
                                                      index_to_coordinates(self.code, self.position, self.line_offset))
        token = ["COND", "ELSE", ""]
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol not in " {":
                self.position -= 1
                raise exceptions.UnexpectedSymbolError(self.advance(),
                                                       index_to_coordinates(self.code, self.position, self.line_offset))
            if symbol == "{":
                break
        loff = index_to_coordinates(self.code, self.position + 1, self.line_offset)[0]
        startpositions = [index_to_coordinates(self.code, self.position, self.line_offset)]
        done = 1
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            if symbol == "}":
                done -= 1
            if symbol == "{":
                done += 1
                startpositions.append(index_to_coordinates(self.code, self.position, self.line_offset))
            if done == 0:
                break
            token[2] += symbol
        if done != 0:
            raise exceptions.NotCompleteCodeBlockError(startpositions)
        parser = Parser(token[2], loff - 1)
        parser.values_names = self.values_names.copy()
        token[2] = parser.parse()
        return token

    def parse(self):
        tokens = []
        cur_token = ""
        self.position = -1
        while self.position < len(self.code) - 1:
            symbol = self.advance()
            cur_token += symbol
            cur_token = cur_token.strip()
            if cur_token == self.rules["IFSTAT"]:
                oldpos = self.position
                while self.position < len(self.code) - 1:
                    symbol = self.advance()
                    if symbol not in " (":
                        self.position = oldpos
                        break
                    if symbol == "(":
                        self.position = oldpos
                        tokens.append(self.make_if_token(tokens[-1]))
                        cur_token = ""
                        break
            elif cur_token in (self.rules["ELSESTAT"] + self.rules["IFSTAT"][0:i] for i in range(0, len(self.rules["IFSTAT"])+1)):
                oldpos = self.position
                while self.position < len(self.code) - 1:
                    symbol = self.advance()
                    if symbol not in " ({"+self.rules["IFSTAT"]:
                        self.position = oldpos
                        break
                    if symbol in self.rules["IFSTAT"]:
                        cur_token += symbol
                    if symbol == "(" and cur_token == self.rules["ELSESTAT"] + self.rules["IFSTAT"]:
                        self.position = oldpos + 2
                        tokens.append(self.make_elseif_token(tokens[-1]))
                        cur_token = ""
                        break
                    elif symbol == "{" and cur_token == self.rules["ELSESTAT"]:
                        self.position = oldpos
                        tokens.append(self.make_else_token(tokens[-1]))
                        cur_token = ""
                        break
                    elif symbol in "({":
                        self.position -= 1
                        raise exceptions.UnexpectedSymbolError(self.advance(),
                                                               index_to_coordinates(self.code, self.position,
                                                                                    self.line_offset))

            elif cur_token in ('int', 'string', 'float'):
                if self.advance() != " ":
                    self.position -= 1
                    raise exceptions.UnexpectedSymbolError(self.advance(),
                                                           index_to_coordinates(self.code, self.position,
                                                                                self.line_offset))
                tokens.append(self.make_func_or_value_token(cur_token))
                cur_token = ""
            elif cur_token in self.values_names:
                tokens.append(self.make_call_or_value_or_func_token(cur_token))
                cur_token = ""
        if cur_token.strip() != "":
            self.position -= 1
            raise exceptions.UnexpectedSymbolError(self.advance(),
                                                   index_to_coordinates(self.code, self.position, self.line_offset))
        return tokens


class Runner:
    def __init__(self):
        self.globals = {}
        self.locals = {0: self.globals}
        self.rules = {}
        self.load_syntax_table(base_syntax_table)

    def load_syntax_table(self, syntax_table):
        for rule in syntax_table.split("\n"):
            try:
                self.rules[rule.split("->")[0].strip()] = "->".join(rule.split("->")[1:]).strip()
            except: pass

    def get_real(self, v, clocals):
        if v[0] == "R":
            return v
        if v[0] == 'NC':
            return 'R', self.eval(v[1], clocals)

    @staticmethod
    def eval(string, clocals):
        try:
            return _eval(string,
                         names=dict(
                             [(n, v[1]) for n, v in filter(lambda v: not isinstance(v[1], MnLFunction) and not isinstance(v[1], PyMnLFunction), clocals.items())]),
                         functions=dict(filter(lambda v: v[1] is MnLFunction or v[1] is PyMnLFunction, clocals.items()))
                         )
        except:
            raise exceptions.EmptyExpressionError()

    def convert(self, svalue, dt, clocals):
        st = svalue
        try:
            st = self.eval(svalue, clocals)
        except BaseException:
            pass
        try:
            for dtype in self.rules["DTYPES"].split("/"):
                dtype, rdt = dtype.split("=")[0], dtype.split("=")[1]
                if rdt == "": continue
                if dt == dtype:
                    st = eval(f"{rdt}({st})")
        except BaseException:
            raise exceptions.ConversionError(st, dt)
        return st

    def run(self, tokens, level=0):
        clocals = self.locals.get(level, self.globals.copy())
        self.locals[level] = clocals
        returnv = None
        lifok = False
        for token in tokens:
            if token[0] == "RETURN":
                returnv = self.get_real(token[1], clocals)
                break
            if token[0] == "SET":
                clocals[token[1]] = self.get_real(token[3], clocals)
            if token[0] == "CALL":
                returnv = clocals[token[1]](
                    *[self.convert(self.get_real(i, clocals)[1], 'var', clocals) for i in token[2]])
            if token[0] == "FUNC":
                clocals[token[2]] = MnLFunction(token[2], token[3], token[4], self, token[1])
            if token[0] == "COND":
                if token[1] == "IF":
                    if not self.eval(token[2], clocals):
                        lifok = False
                        continue
                    lifok = True
                    returnv = self.run(token[3], level)
                if token[1] == "EIF" and not lifok:
                    if not self.eval(token[2], clocals):
                        lifok = False
                        continue
                    lifok = True
                    returnv = self.run(token[3], level)
                if token[1] == "ELSE" and not lifok:
                    returnv = self.run(token[2], level)
        return returnv


class MnLFunction:
    def __init__(self, name, args, code, runner, return_type):
        self.name = name
        self.args = args
        self.func = code
        self.runner = runner
        self.return_type = return_type

    def __call__(self, *args):
        rargs = list(zip(self.args, args))
        parser = Parser('\0'.join([str(i[1]) for i in rargs]) + '\0')
        atokens = []
        for i in rargs:
            atokens.append(['SET', i[0], 'var', parser.make_value_subtoken('\0', 'var')])
            parser.advance()
        lvl = random.randint(100000000, 999999999)
        ret = self.runner.run(atokens + self.func, lvl)
        self.runner.locals[lvl] = {}
        return ret

class LegacyModuleLib(MnLLibrary):
    def __init__(self):
        self.namespace = {}
        self.initialized = True
        self.need_cleanup = False


class MnLEngine:
    def __init__(self):
        self.loaded_libs = []
        self.syntax_table = base_syntax_table
        self.persisting_globals = False
        self.__locals = {"runner": {}, "parser": []}

    def reinit(self):
        return self.__init__()

    def load_module(self, module):
        if not hasattr(module, "code_globals"):
            raise UnexpectedInput("This does not look like legacy MnL module! If you are trying to load library, use \"engine.load_library\" method!")

        lib = LegacyModuleLib()
        from . import legacy_util as l_util
        for i in module.code_globals:
            if i is not l_util.PyMnLAdapter:
                continue
            lib.functions.append(PyMnLFunction(i.func.__name__, i.func))
        self.loaded_libs.append(lib())
        return

    def load_library(self, library):
        lib = library()
        self.loaded_libs.append(lib)
        return lib.init()

    def load_syntax_table(self, st):
        self.syntax_table += st + "\n"

    def run(self, code):
        parser = Parser(code)
        parser.load_syntax_table(self.syntax_table)
        runner = Runner()
        runner.load_syntax_table(self.syntax_table)
        runner.loaded_libs = self.loaded_libs

        print(runner.globals)
        print(parser.values_names)

        if self.persisting_globals:
            runner.globals = self.__locals["runner"].copy()
            runner.locals[0] = runner.globals
            parser.values_names = self.__locals["parser"].copy()

        print(runner.globals)
        print(parser.values_names)

        for lib in self.loaded_libs:
            if lib.need_cleanup:
                lib.cleanup()
            if not lib.initialized:
                lib.init()
            for key, value in lib.namespace.items():
                parser.values_names.append(key)
                runner.globals[key] = value

        runner.run(parser.parse())

        print(runner.globals)
        print(parser.values_names)

        if self.persisting_globals:
            self.__locals["parser"] = parser.values_names.copy()
            self.__locals["runner"] = runner.globals.copy()
        else:
            self.__locals = {"runner": {}, "parser": []}

    def __str__(self=None):
        return "MnLEngine_v4"
