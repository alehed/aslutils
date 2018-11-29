from .ASLParser import ASLParser
from .ASLVisitor import ASLVisitor


class ValueVisitor(ASLVisitor):
    # Visits expressions and either returns the constant value or None.

    def __init__(self, parent):
        self.parent = parent

    def visitExpression(self, ctx: ASLParser.ExpressionContext):
        type = self.parent.type_visitor.visit(ctx)
        if not type:
            return None
        if ctx.expression(0):
            val1 = self.visit(ctx.expression(0))
            if not val1:
                return None
        if ctx.expression(1):
            val2 = self.visit(ctx.expression(1))
            if not val2:
                return None
        if ctx.If():
            if val1:
                return self.visit(ctx.expression(1))
            else:
                return self.visit(ctx.expression(2))
        elif ctx.literal():
            return self.visit(ctx.literal())
        elif not ctx.Identifier() and ctx.LeftParen() and ctx.Comma():
            return None
        elif not ctx.Identifier() and ctx.LeftParen():
            return val1
        elif ctx.Identifier() and ctx.LeftParen():
            return None
        elif ctx.LeftBracket():
            return None
        elif not ctx.In() and ctx.LeftBrace():
            return None
        elif ctx.Dot():
            return None
        elif ctx.Not():
            return ~val1
        elif ctx.Plus() or ctx.Minus():
            if ctx.expression(1):
                return val1 + val2 if ctx.Plus() else val1 - val2
            else:
                if ctx.Minus():
                    return -val1
                else:
                    return val1
        elif ctx.Negation():
            val = self.visit(ctx.expression(0))
            return not val
        elif ctx.Colon():
            type2 = self.parent.type_visitor.visit(ctx.expression(1))
            return val2 + (val1 << type2.value)
        elif ctx.Mult():
            return val1 * val2
        elif ctx.Div():
            return val1 // val2
        elif ctx.Mod():
            return val1 % val2
        elif ctx.Divide():
            return val1 / val2
        elif ctx.LeftShift() or ctx.RightShift():
            return val1 << val2 if ctx.LeftShift else val1 >> val2
        elif ctx.Equal() or ctx.NotEqual():
            return val1 == val2 if ctx.Equal() else val1 != val2
        elif ctx.Greater() or ctx.Less():
            return val1 > val2 if ctx.Greater() else val1 < val2
        elif ctx.GreaterEqual() or ctx.LessEqual():
            return val1 >= val2 if ctx.GreaterEqual() else val1 <= val2
        elif ctx.Land() or ctx.Lor():
            return val1 and val2 if ctx.Land() else val1 or val2
        elif ctx.And() or ctx.Or() or ctx.Eor():
            if ctx.And():
                return val1 & val2
            elif ctx.Or():
                return val1 | val2
            else:
                return val1 ^ val2
        elif ctx.In():
            exprs = list(map(lambda x: self.visit(x), ctx.expression()))
            return exprs[0] in exprs[1:]
        elif ctx.Unknown():
            return None
        elif ctx.Identifier():
            identifierString = ctx.Identifier().getText()
            if identifierString in self.parent.variables:
                return self.parent.variables[identifierString][2]
            else:
                return None
        else:
            assert False
            return None

    def visitLiteral(self, ctx: ASLParser.LiteralContext):
        if ctx.Integer():
            return int(ctx.Integer().getText())
        elif ctx.Hex():
            return int(ctx.Hex().getText(), 16)
        elif ctx.BitVector():
            pattern = ctx.BitVector().getText()[1:-1].translate({ord(' '): ''})
            return int('0b' + pattern, 2)
        elif ctx.BitMask():
            pattern = ctx.BitMask().getText()[1:-1].translate({ord('x'): '0', ord(' '): ''})
            return int('0b' + pattern, 2)
        elif ctx.FixedPointNum():
            return float(ctx.FixedPointNum().getText())
        elif ctx.Bool():
            return bool(ctx.Bool().getText().title())
        else:
            return ctx.String().getText()
