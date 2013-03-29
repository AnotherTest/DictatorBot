from pyparsing import quotedString, Word, alphas, alphanums, Suppress,\
    Optional, Forward, OneOrMore, ZeroOrMore, nums, ParseFatalException,\
    Token
import re, inspect, types, pickle, exceptions
from Utils import enum, find, httpGet
import os.path

TokenType = enum("StrLit", "NumLit", "Var", "Call", "Def", "End")

def getEbnfParser(symbols):
    identifier = Word(alphas + '_', alphanums + '_')
    string = quotedString.setParseAction(
        lambda t: symbols.append((t[0][1:-1], TokenType.StrLit))
    )
    integer = Word(nums).setParseAction(
        lambda t: symbols.append((int(t[0]), TokenType.NumLit))
    )
    var = Suppress("$") + identifier
    var.setParseAction(
        lambda t: symbols.append((t[0], TokenType.Var))
    )
    literal = var | string | integer
    fnid = Suppress(Optional(".")) + identifier
    fnid.setParseAction(
        lambda t: symbols.append((t[0], TokenType.Call))
    )
    call = Forward()
    callb = fnid + ZeroOrMore(call | literal)
    call << ((Suppress("(") + callb + Suppress(")")) | callb)
    fndef_head = Suppress("let") + identifier
    fndef_head.setParseAction(
        lambda t: symbols.append((t[0], TokenType.Def))
    )
    definition = fndef_head + ZeroOrMore(var) + Suppress("=") + call
    cmd = OneOrMore((definition | call) + Word(";").setParseAction(
        lambda t: symbols.append((t[0], TokenType.End))
    ))
    msg = OneOrMore(cmd)
    return msg

def isLiteral(tk):
    t = tk[1]
    return t == TokenType.StrLit or t == TokenType.NumLit


class Interpreter:
    function_table = {
        "id"     : lambda x: x,
        "uc"     : lambda x: x.upper(),
        "lc"     : lambda x: x.lower(),
        "add"    : lambda x, y: x + y,
        "mul"    : lambda x, y: x * y,
        "div"    : lambda x, y: x / y,
        "pow"    : lambda x, y: x ** y,
        "nil"    : lambda x: None,
        "grep"   : lambda ex, s: re.search(ex, s).group(),
        "grepi"  : lambda ex, s, i: re.search(ex, s).groups()[i],
        "get"    : lambda url: httpGet(url)
    }
    user_function_table = {}
    _tokens = [] # Current list of tokens
    _filename = ""

    def __init__(self, filename):
        """
        Constructor, just creates a functions file if it doesn't exist.
        """
        self._filename = filename
        if not os.path.isfile(filename):
            self.saveUserFunctions()

    def fnGetArgc(self, name):
        """Gets the amount of arguments a function given by its name takes."""
        if name in self.function_table:
            return len(inspect.getargspec(self.function_table[name]).args)
        else:
            return len(self.user_function_table[name][0])

    def getArgTuple(self, arg):
        """Gets the tuple (value, TokenType) associated with a given argument."""
        if type(arg) == types.StringType:
            return (arg, TokenType.StrLit)
        else:
            return (arg, TokenType.IntLit)

    def fnCall(self, name, args):
        """Calls a function given its name and arguments."""
        if name in self.function_table:
            return self.function_table[name](*args)
        # user defined function: insert code to execute in tokens
        fn = self.user_function_table[name]
        for x in fn[1]:
            if x[1] == TokenType.Var:
                index = find(x[0], fn[0])
                if index == None:
                    # TODO: ERROR
                    pass
                self._tokens.insert(0, self.getArgTuple(args[index]))
            else:
                self._tokens.insert(0, x)
        return self.interpretStatement() 

    def fnDef(self, name):
        """Handles function definition."""
        args = []
        while self._tokens[0][1] == TokenType.Var:
            args.append(self._tokens.pop(0)[0])
        code = []
        while self._tokens[0][1] != TokenType.End:
            code.append(self._tokens.pop(0))
        code.reverse()
        self.user_function_table[name] = (args, code)

    def interpretStatement(self):
        head = self._tokens.pop(0)
        if isLiteral(head):
            return head[0]
        if head[1] == TokenType.Def:
            return self.fnDef(head[0])
        argc = self.fnGetArgc(head[0])
        args = [None] * argc
        for j in range(argc):
            args[j] = self.interpretStatement()
        return self.fnCall(head[0], args)

    def saveUserFunctions(self):
        with open(self._filename, "wb") as f:
            pickle.dump(self.user_function_table, f)

    def loadUserFunctions(self):
        with open(self._filename, "rb") as f:
            self.user_function_table = pickle.load(f)

    def interpret(self, tokens):
        self.loadUserFunctions()
        last, end_token = 0, (";", TokenType.End)
        find_end = lambda: find(end_token, tokens[last:]) + last + 1
        output = []
        amount = tokens.count(end_token)
        for i in range(amount):
            new = find_end()
            try:
                self._tokens = tokens[last:new]
                output.append(self.interpretStatement())
            except:
                output.append("Oops, seems like something went wrong.")
                raise
            last, new = new, find_end()
        self.saveUserFunctions()
        return output
