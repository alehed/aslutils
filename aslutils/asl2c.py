from .asl2 import asl_to_lang
from .ASLParser import ASLParser
from .ASLVisitor import ASLVisitor
from .asl_type import ASLType
from .asl_type_visitor import ASLTypeVisitor
from .asl_value_visitor import ASLValueVisitor


class CVisitor(ASLVisitor):
    """(Internal) Class that generates C code from ASL Code

    Externally, this should not be used directly, but via :func:`asl_to_c`.

    The entry method for parsing should always be :func:`visitStart`. Since the
    visitor keeps track of variables, for each call to :func:`visitStart` a
    fresh object should be used.

    The methods return the generated C code as a [str]. Note that no code is
    generated for variables that are simply assigned to constants. So in order
    to generate the "full" valid code for the ASL snippet it is possible that
    the content of :attr:`self.variables` also has to be taken into account.

    :param variables: A mapping from name to (type: ASLType or None, value) for
                      all pre-existing variables. This is needed so that when
                      assigning to one of those variables it is not redeclared
                      as ASL is somewhat like python with respect to var
                      declarations.
    :type variables: {str: (ASLType or None, Any or None)}

    :ivar self.variables: A mapping from variable name to a tuple containing: a
                     bool which signifies whether the variable already existed
                     before the snippet (in this order), the type of the
                     variable as an ASLType or None if unknown. The constant
                     value of the variable or None if unknown.
    :vartype self.variables: {str: (bool, ASLType or None, Any or None)}
    """

    def __init__(self, variables):
        self.variables = {key: (True, value[0], value[1]) for (key, value) in variables.items()}
        self.value_visitor = ASLValueVisitor(self)
        self.type_visitor = ASLTypeVisitor(self)

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
                # TODO: Handle bitpatterns correctly
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
        elif ctx.BitPattern():
            pattern = ctx.BitPattern().getText()[1:-1].translate({ord(' '): '', ord('x'): '0'})
            return '0b' + pattern
        elif ctx.FixedPointNum():
            return ctx.FixedPointNum().getText()
        elif ctx.Bool():
            return ctx.Bool().getText().lower()
        else:
            return ctx.String().getText()

    def visitErrorNode(self, node):
        raise Exception("Error")


def asl_to_c(string, fields):
    """Converts the given processed ASL string into a c program snippet

    Calls :func:`asl_to_lang`, for more information check it's documentation.

    :param string: ASL snippet string. The ASL code has to contain special
                   tokens for structure instead of indentation and newlines.
    :type string: str
    :param fields: A list of fields, each specified by a name and a length (in
                   bits).
    :type fields: [(str, int)]

    :returns: A pair containing a variable map and the generated c code. The
              variable map maps from variable name to if it already existed
              before the snippet, its type (if known) and its value (if it's a
              known constant).
    :rtype: ({str: (bool, ASLType or None, Any)}, [str])
    """

    return asl_to_lang(string, fields, CVisitor)
