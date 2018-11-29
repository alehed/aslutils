from .ASLParser import ASLParser
from .ASLVisitor import ASLVisitor
from .ASLType import ASLType


class TypeVisitor(ASLVisitor):
    # Visits expressions and returns a ASLType or None. Does typechecking.

    def __init__(self, parent):
        self.parent = parent

    def visitExpression(self, ctx: ASLParser.ExpressionContext):
        if ctx.expression(0):
            type1 = self.visit(ctx.expression(0))
        if ctx.expression(1):
            type2 = self.visit(ctx.expression(1))
        if ctx.If():
            if type2 is not None:
                return type2
            else:
                return self.visit(ctx.expression(2))
        elif ctx.literal():
            return self.visit(ctx.literal())
        elif not ctx.Identifier() and ctx.LeftParen() and ctx.Comma():
            return None
        elif not ctx.Identifier() and ctx.LeftParen():
            return self.visit(ctx.expression(0))
        elif ctx.Identifier() and ctx.LeftParen():
            function = ctx.Identifier().getText()
            if function == "Replicate":
                assert type1 == ASLType.Kind.bits
                arg2_val = self.parent.value_visitor.visit(ctx.expression(1))
                if type1.value is not None and arg2_val is not None:
                    return ASLType(ASLType.Kind.bits, type1.value * arg2_val)
                else:
                    return None
            if function == "Zeros":
                assert type1 == ASLType.Kind.int
                arg_val = self.parent.value_visitor.visit(ctx.expression(0))
                return ASLType(ASLType.Kind.bits, arg_val)
            if function == "UInt":
                return ASLType(ASLType.Kind.int)
            if function == "ZeroExtend":
                arg_val = self.parent.value_visitor.visit(ctx.expression(0))
                return ASLType(ASLType.Kind.bits, arg_val)
            if function == "SignExtend":
                arg_val = self.parent.value_visitor.visit(ctx.expression(0))
                return ASLType(ASLType.Kind.bits, arg_val)
            if function == "T32ExpandImm" or function == "A32ExpandImm":
                return ASLType(ASLType.Kind.bits, 32)
            if function == "AdvSIMDExpandImm":
                return ASLType(ASLType.Kind.bits, 64)
            else:
                return None
        elif ctx.LeftBracket():
            return None
        elif not ctx.In() and ctx.LeftBrace():
            if ctx.Dot():
                assert False
                return None
            else:
                cur_idx = ctx.getChildCount() - 3
                total_bits = 0
                while True:
                    expr_type = self.visit(ctx.getChild(cur_idx + 1))
                    assert not expr_type or expr_type == ASLType.Kind.int
                    if ctx.getChild(cur_idx).getSymbol().type == ASLParser.RangeDown:
                        min_slice = self.visit(ctx.getChild(cur_idx - 1))
                        assert not min_slice or min_slice == ASLType.Kind.int
                        expr_val = self.parent.value_visitor.visit(ctx.getChild(cur_idx + 1))
                        min_val = self.parent.value_visitor.visit(ctx.getChild(cur_idx - 1))
                        if (expr_val is not None) and (min_val is not None):
                            total_bits += expr_val - min_val
                        else:
                            total_bits = None
                            break
                    else:
                        total_bits += 1
                    if ctx.getChild(cur_idx).getSymbol().type == ASLParser.LeftBrace:
                        break
                    else:
                        cur_idx -= 2
                return ASLType(ASLType.Kind.bits, total_bits)
        elif ctx.Dot():
            identName = ctx.Identifier().getText()
            if identName in self.parent.variables:
                return self.parent.variables[identName][1]
            else:
                return None
        elif ctx.Not():
            return type1
        elif ctx.Plus() or ctx.Minus():
            if type1 is not None:
                return type1
            else:
                return type2
        elif ctx.Negation():
            return ASLType(ASLType.Kind.bool)
        elif ctx.Colon():
            return ASLType(ASLType.Kind.bits, type1.value + type2.value)
        elif ctx.Mult():
            if type1 is None:
                return type2
            elif type2 is None:
                return type1
            elif type1 != type2:
                return ASLType(ASLType.Kind.real)
            else:
                return type1
        elif ctx.Div():
            if type1 is not None:
                return type1
            else:
                return type2
        elif ctx.Mod():
            if type2 is not None:
                return type2
            else:
                return type1
        elif ctx.Divide():
            return ASLType(ASLType.Kind.real)
        elif ctx.LeftShift() or ctx.RightShift():
            return ASLType(ASLType.Kind.int)
        elif ctx.Equal() or ctx.NotEqual() or ctx.Greater() or ctx.Less() \
                or ctx.GreaterEqual() or ctx.LessEqual() or ctx.Land() or ctx.Lor():
            return ASLType(ASLType.Kind.bool)
        elif ctx.And() or ctx.Or() or ctx.Eor():
            if type1 is not None:
                return type1
            else:
                return type2
        elif ctx.In():
            return ASLType(ASLType.Kind.bool)
        elif ctx.Unknown():
            return self.visit(ctx.typeName())
        elif ctx.Identifier():
            identifierString = ctx.Identifier().getText()
            if identifierString in self.parent.variables:
                return self.parent.variables[identifierString][1]
            else:
                return None
        else:
            assert False
            return None

    def visitLiteral(self, ctx: ASLParser.LiteralContext):
        if ctx.Integer() or ctx.Hex():
            return ASLType(ASLType.Kind.int)
        elif ctx.BitVector():
            pattern = ctx.BitVector().getText()[1:-1].translate({ord(' '): ''})
            return ASLType(ASLType.Kind.bits, len(pattern))
        elif ctx.BitMask():
            pattern = ctx.BitMask().getText()[1:-1].translate({ord('x'): '0', ord('0'): '1', ord(' '): ''})
            return ASLType(ASLType.Kind.bitmask, int(pattern, 2))
        elif ctx.FixedPointNum():
            return ASLType(ASLType.Kind.real)
        elif ctx.Bool():
            return ASLType(ASLType.Kind.bool)
        else:
            return ASLType(ASLType.Kind.other)

    def visitTypeName(self, ctx: ASLParser.TypeNameContext):
        if ctx.IntegerType():
            return ASLType(ASLType.Kind.int)
        elif ctx.BooleanType():
            return ASLType(ASLType.Kind.bool)
        elif ctx.BitsType():
            size = self.parent.value_visitor.visit(ctx.expression())
            return ASLType(ASLType.Kind.bits, size)
        elif ctx.BitType():
            return ASLType(ASLType.Kind.bits, 1)
        elif ctx.RealType():
            return ASLType(ASLType.Kind.real)
        else:
            return ASLType(ASLType.Kind.other)
