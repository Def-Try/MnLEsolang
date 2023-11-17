class BaseError(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.message}"

class UnexpectedSymbolError(BaseError):
    def __init__(self, symbol, position):
        super().__init__(f"Unexpected symbol '{symbol.encode('utf-8').__str__()[2:-1]}' at line {position[0]} char {position[1]}")

class NotCompleteCodeBlockError(BaseError):
    def __init__(self, startpositions):
        super().__init__(f"Code block was not closed. Possible issue locations at position(s) {', '.join(['('+str(i[0])+','+str(i[1])+')' for i in startpositions])}")

class UnexpectedStatementError(BaseError):
    def __init__(self, statement, position):
        super().__init__(f"Unexpected statement \"{statement}\" at line {position[0]} char {position[1]}")

class ConversionError(BaseError):
    def __init__(self, value, dt, position=None):
        super().__init__(f"Unable to convert value \"{value.encode('utf-8').__str__()[2:-1]}\" to data type {dt}" + (f" at line {position[0]} char {position[1]}" if position else ""))

class EmptyExpressionError(BaseError):
    def __init__(self):
        super().__init__(f"Empty expression found (unable to trace)")