from antlr4 import InputStream, CommonTokenStream
from .ASLLexer import ASLLexer
from .ASLParser import ASLParser
from .asl_type import ASLType


def asl_to_lang(string, fields, LangVisitor):
    """Converts the given processed ASL string into a code snippet

    For instance the following ASL code::

        integer bits_d = 4;
        integer bits_f = 5 * UInt(op) + 3;

    Will be processed to::

        integer bits_d = 4; NEWLINE integer bits_f = 5 * op + 3;

    Assuming op is a 5 bit field declared before, the processed code along with:
    `[(op, 5)]` will be passed into :func:`asl_to_lang`. The result of the
    function call would be the string (in the case of a c visitor)::

        int64_t bits_f = 5 * (u_int64_t)op + 3;

    And the variable table::

        {'op': (True, ASLType(ASLType.Kind.bits, 5), None),
         'bits_d': (False, ASLType(ASLType.Kind.int), 4),
         'bits_f': (False, ASLType(ASLType.Kind.int), None)}

    Note that the code for `bits_d` is not generated but this information is
    passed out via the variable table.

    :param string: ASL snippet string. The ASL code has to contain special
                   tokens for structure instead of indentation and newlines.
    :type string: str
    :param fields: A list of fields, each specified by a name and a length (in
                   bits).
    :type fields: [(str, int)]
    :param LangVisitor: The visitor class to use on the ast
    :type LangVisitor: class

    :returns: A pair containing a variable map and the generated c code. The
              variable map maps from variable name to if it already existed
              before the snippet, its type (if known) and its value (if it's a
              known constant).
    :rtype: ({str: (bool, ASLType or None, Any)}, [str])
    """

    input = InputStream(string)
    lexer = ASLLexer(input)
    stream = CommonTokenStream(lexer)
    parser = ASLParser(stream)
    tree = parser.start()
    variables = {}
    for field in fields:
        variables[field[0]] = (ASLType(ASLType.Kind.bits, field[1]), None)
    visitor = LangVisitor(variables)
    generated_code = visitor.visit(tree)
    return visitor.variables, generated_code
