from antlr4 import InputStream, CommonTokenStream
from .ASLLexer import ASLLexer
from .ASLParser import ASLParser
from .ASLVisitor import ASLVisitor
from .ASLType import ASLType
from .typevisitor import TypeVisitor
from .valuevisitor import ValueVisitor


class MyVisitor(ASLVisitor):

    def __init__(self, variables):
        # maps name to (don't generate, type, value)
        self.variables = variables
        self.value_visitor = ValueVisitor(self)
        self.type_visitor = TypeVisitor(self)

    def visitStart(self, ctx: ASLParser.StartContext):
        result = []
        for statement in ctx.statement():
            result += self.visit(statement)
        return result

    def visitStatement(self, ctx: ASLParser.StatementContext):
        result = []
        if ctx.simpleStatement():
            return self.visit(ctx.simpleStatement())
        elif ctx.If():
            result.append("if ({0}) {{".format(self.visit(ctx.expression(0))))
            result += self.visit(ctx.block(0))
            result.append("}")
            for i in range(len(ctx.Elsif())):
                result.append("else if ({0}) {{".format(self.visit(ctx.expression(i+1))))
                result += self.visit(ctx.block(i+1))
                result.append("}")
            if ctx.Else():
                result.append("else {")
                result += self.visit(ctx.block()[-1])
                result.append("}")
        elif ctx.Case():
            expr = self.visit(ctx.expression(0))
            first = True
            for i in range(len(ctx.When())):
                literal_or_ident = self.visit(ctx.getChild(i*3 + 5))
                if first:
                    result.append("if (({0}) == {1}) {{".format(expr, literal_or_ident))
                    first = False
                else:
                    result.append("else if (({0}) == {1}) {{".format(expr, literal_or_ident))
                result += self.visit(ctx.block(i))
                result.append("}")
            if ctx.Otherwise():
                result.append("else {")
                result += self.visit(ctx.block()[-1])
                result.append("}")
        else:
            print(ctx.getText())
            assert False
        return result

    def visitSimpleStatement(self, ctx: ASLParser.SimpleStatementContext):
        result = []
        if ctx.assignableExpr():
            if ctx.Assign():
                name = self.visit(ctx.assignableExpr(0))
                if not name:
                    return result
                if not ctx.typeName():
                    if name in self.variables:
                        type = self.variables[name][1]
                    else:
                        type = self.type_visitor.visit(ctx.expression(0))
                else:
                    type = self.type_visitor.visit(ctx.typeName())
                expr_code = self.visit(ctx.expression(0))
                if type is None:
                    print("Warning: Could not find type of", ctx.getText(), "assuming bits")
                    type = ASLType(ASLType.Kind.bits)
                if name not in self.variables:
                    self.variables[name] = (False, type, self.value_visitor.visit(ctx.expression(0)))
                    if self.variables[name][2] is None:
                        result.append("{0} {1} = {2};".format(type.c_type(), name, expr_code))
                else:
                    result.append("{0} = {1};".format(name, expr_code))
            else:
                for var in ctx.assignableExpr():
                    name = self.visit(var)
                    type = self.type_visitor.visit(ctx.typeName())
                    result.append("{0} {1};".format(type.c_type(), name))
                    self.variables[name] = (False, type, None)
        elif ctx.Undefined():
            result.append("undefined();")
        elif ctx.Unpredictable():
            result.append("unpredictable();")
        elif ctx.See():
            result.append("// see {0}".format(self.visit(ctx.expression(0))))
        elif ctx.Assert():
            result.append("assert({0});".format(self.visit(ctx.expression(0))))
        elif ctx.LeftParen():
            args = list(map(lambda x: self.visit(x), ctx.expression()))
            result.append("// {0}({1});".format(ctx.Identifier(0).getText(), ", ".join(args)))
        else:
            print(ctx.getText())
            assert False
        return result

    def visitBlock(self, ctx: ASLParser.BlockContext):
        stmts = []
        if ctx.Start():
            for statement in ctx.statement():
                stmts += self.visit(statement)
        else:
            for simpleStatement in ctx.simpleStatement():
                stmts += self.visit(simpleStatement)
        return list(map(lambda s: "    " + s, stmts))

    def visitExpression(self, ctx: ASLParser.ExpressionContext):
        # make sure that there are no type errors
        type = self.type_visitor.visit(ctx)
        # check to see if we can skip code generation and directly insert
        val = self.value_visitor.visit(ctx)
        if val:
            if type == ASLType.Kind.bool:
                return str(val).lower()
            else:
                return str(val)
        if ctx.expression(0):
            text1 = self.visit(ctx.expression(0))
        if ctx.expression(1):
            text2 = self.visit(ctx.expression(1))
        if ctx.If():
            text3 = self.visit(ctx.expression(2))
            return "({0}) ? ({1}) : ({2})".format(text1, text2, text3)
        elif ctx.literal():
            return self.visit(ctx.literal())
        elif not ctx.Identifier() and ctx.LeftParen() and ctx.Comma():
            assert False
            return ""
        elif not ctx.Identifier() and ctx.LeftParen():
            return text1
        elif ctx.Identifier() and ctx.LeftParen():
            args = list(map(lambda x: self.visit(x), ctx.expression()))
            return "{0}({1})".format(ctx.Identifier().getText(), ", ".join(args))
        elif ctx.LeftBracket():
            args = list(map(lambda x: self.visit(x), ctx.expression()))
            return "{0}[{1}]".format(ctx.Identifier().getText(), ", ".join(args))
        elif not ctx.In() and ctx.LeftBrace():
            if ctx.Dot():
                assert False
                return None
            else:
                cur_idx = ctx.getChildCount() - 3
                total_bits = "0"
                slices = []
                while True:
                    expr_text = self.visit(ctx.getChild(cur_idx + 1))
                    if ctx.getChild(cur_idx).getSymbol().type == ASLParser.RangeDown:
                        min_slice = self.visit(ctx.getChild(cur_idx - 1))
                        length = "({0}) - ({1})".format(expr_text, min_slice)
                    else:
                        length = "1"
                    slices.append("(({0}) >> (({1}) - ({3}) - ({2}))) & ({3})".format(text1, expr_text, total_bits, length))
                    total_bits += " + ({0})".format(length)
                    if ctx.getChild(cur_idx).getSymbol().type == ASLParser.LeftBrace:
                        break
                    else:
                        cur_idx -= 2
                return " | ".join(slices)
        elif ctx.Dot():
            return "{0}.{1}".format(self.visit(ctx.expression(0)), ctx.Identifier().getText())
        elif ctx.Not():
            text = self.visit(ctx.expression(0))
            return "~({0})".format(text)
        elif ctx.Plus() or ctx.Minus():
            if ctx.expression(1):
                formatstr = "({0}) + ({1})" if ctx.Plus() else "({0}) - ({1})"
                return formatstr.format(text1, text2)
            elif ctx.Minus():
                return "-" + text1
            else:
                return text
        elif ctx.Negation():
            return "!({})".format(self.visit(ctx.expression(0)))
        elif ctx.In():
            exprs = list(map(lambda x: self.visit(x), ctx.expression()))
            strs = []
            for i in range(1, len(exprs)):
                strs.append("({0}) == ({1})".format(exprs[0], exprs[i]))
            return " || ".join(strs)
        elif ctx.Unknown():
            return "0"
        elif ctx.Identifier():
            return ctx.Identifier().getText()
        elif ctx.Colon():
            type2 = self.type_visitor.visit(ctx.expression(1))
            return "({0}) + (({1}) << ({2}))".format(text2, text1, type2.value)
        else:
            if ctx.Mult():
                operator = "*"
            elif ctx.Div() or ctx.Divide():
                operator = "/"
            elif ctx.Mod():
                operator = "%"
            elif ctx.LeftShift():
                operator = "<<"
            elif ctx.RightShift():
                operator = ">>"
            elif ctx.Equal():
                operator = "=="
            elif ctx.NotEqual():
                operator = "!="
            elif ctx.Greater():
                operator = ">"
            elif ctx.Less():
                operator = "<"
            elif ctx.GreaterEqual():
                operator = ">="
            elif ctx.LessEqual():
                operator = "<="
            elif ctx.Land():
                operator = "&&"
            elif ctx.Lor():
                operator = "||"
            elif ctx.And():
                operator = "&"
            elif ctx.Or():
                operator = "|"
            elif ctx.Eor():
                operator = "^"
            else:
                assert False
                operator = ""
            return "({0}) {2} ({1})".format(text1, text2, operator)

    def visitAssignableExpr(self, ctx: ASLParser.AssignableExprContext):
        if ctx.Identifier() and not ctx.LeftBracket():
            return ctx.Identifier().getText()
        else:
            return None

    def visitLiteral(self, ctx: ASLParser.LiteralContext):
        if ctx.Integer():
            return ctx.Integer().getText()
        elif ctx.Hex():
            return ctx.Hex().getText()
        elif ctx.BitVector():
            pattern = ctx.BitVector().getText()[1:-1]
            return '0b' + pattern.translate({ord(' '): ''})
        elif ctx.BitMask():
            pattern = ctx.BitMask().getText()[1:-1].translate({ord('x'): '0'})
            return '0b' + pattern
        elif ctx.FixedPointNum():
            return ctx.FixedPointNum().getText()
        elif ctx.Bool():
            return ctx.Bool().getText().lower()
        else:
            return ctx.String().getText()

    def visitErrorNode(self, node):
        raise Exception("Error")


def parse_asl(string, fields):
    input = InputStream(string)
    lexer = ASLLexer(input)
    stream = CommonTokenStream(lexer)
    parser = ASLParser(stream)
    tree = parser.start()
    # lisp_tree_str = tree.toStringTree(recog=parser)
    # print(lisp_tree_str)
    variables = {}
    for field in fields:
        variables[field[0]] = (True, ASLType(ASLType.Kind.bits, field[1]), None)
    visitor = MyVisitor(variables)
    generated_code = visitor.visit(tree)
    return visitor.variables, generated_code
