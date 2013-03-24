from pyparsing import quotedString, Word, alphas, alphanums, Suppress,\
    Optional, Forward, OneOrMore, ZeroOrMore, nums, ParseFatalException,\
    Token
import inspect, types, pickle, exceptions
from Utils import enum, find

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

function_table = {
    "id"     : lambda x: x,
    "uc"     : lambda x: x.upper(),
    "lc"     : lambda x: x.lower(),
    "ad"     : lambda x, y: x + y,
    "ml"     : lambda x, y: x * y,
    "dv"     : lambda x, y: x / y,
    "nl"     : lambda x: return None
}

user_function_table = {}

def isLiteral(tk):
    t = tk[1]
    return t == TokenType.StrLit or t == TokenType.NumLit

def fnGetArgc(name):
    global function_table, user_function_table
    if name in function_table:
        return len(inspect.getargspec(function_table[name]).args)
    return len(user_function_table[name][0])

def getArgTuple(arg):
    if type(arg) == types.StringType:
        return (arg, TokenType.StrLit)
    else:
        return (arg, TokenType.IntLit)

def fnCall(name, args, tokens):
    global function_table, user_function_table
    print "%s called, is user function?" % name, name in user_function_table
    if name in user_function_table: print user_function_table[name] 
    if name in function_table:
        return function_table[name](*args)
    # user defined function: insert code to execute in tokens
    fn = user_function_table[name]
    # reverse code because we must insert in correct order
    print "Before: ", tokens
    for x in fn[1]:
        if x[1] == TokenType.Var:
            index = find(x[0], fn[0])
            if index == None:
                # TODO: ERROR
                pass
            tokens.insert(0, getArgTuple(args[index]))
        else:
            tokens.insert(0, x)
    print "After: ", tokens
    return interpretStatement(tokens) 

def fnDef(name, tokens):
    global user_function_table
    args = []
    while tokens[0][1] == TokenType.Var:
        args.append(tokens.pop(0)[0])
    code = []
    while tokens[0][1] != TokenType.End:
        code.append(tokens.pop(0))
    code.reverse()
    user_function_table[name] = (args, code)

def interpretStatement(tokens):
    global function_table
    head = tokens.pop(0)
    if isLiteral(head):
        return head[0]
    if head[1] == TokenType.Def:
        return fnDef(head[0], tokens)
    argc = fnGetArgc(head[0])
    args = [None] * argc
    for j in range(argc):
        args[j] = interpretStatement(tokens)
    return fnCall(head[0], args, tokens)

def saveUserFunctions():
    global user_function_table
    pickle.dump(user_function_table, open("functions.p", "wb"))

def loadUserFunctions():
    global user_function_table
    try:
        with open("functions.p", "rb") as f:
            user_function_table = pickle.load(f)
    except exceptions.IOError as e:
        if e.errno == 2:
             saveUserFunctions()
        else:
            raise

def interpret(tokens):
    loadUserFunctions()
    last, end_token = 0, (";", TokenType.End)
    find_end = lambda: find(end_token, tokens[last:]) + last + 1
    output = []
    amount = tokens.count(end_token)
    for i in range(amount):
        new = find_end()
        try:
            output.append(interpretStatement(tokens[last:new]))
        except:
            output.append("Oops, seems like something went wrong.")
        last, new = new, find_end()
    saveUserFunctions()
    return output
