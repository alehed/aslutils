import re
import sys


def mask_bits(bitstring):
    """Returns an int corresponding to the bitmask of the bitpattern

    For example "100xx01" is translated to 0b1110011.

    :returns: The integer value where only don't cares are mapped to 0
    :rtype: int
    """

    return int(bitstring.translate({ord('x'): '0', ord('0'): '1'}), 2)


def value_bits(bitstring):
    """Returns an int corresponding to the value of the bitpattern

    For example "100xx01" is translated to 0b1000001.

    :returns: The integer value of the bit pattern interpreted without don't care values
    :rtype: int
    """

    return int(bitstring.translate({ord('x'): '0'}), 2)


class CaseField():
    """Represents one field of a case statement

    An example case statement line with 3 fields::

        case (op, 25 +: 3, id_t) of

    The class represents one of the following:

     * A named field (if intialized with "op" or "id_t").
     * An implicit range (if initialized with "25 +: 3").

    The result of initializing with invalid input is not defined.

    :param str_repr: The string in ASL syntax, it does not contain the comma or paren
    :type str_repr: str

    :ivar self.name: The name of the field if named field
    :vartype self.name: str or None
    :ivar self.start: The start of the implicit range if implicit range
    :vartype self.start: int or None
    :ivar self.run: The run of the implicit range if implicit range
    :vartype self.run: int or None
    """

    def __init__(self, str_repr):
        self.name = None
        self.start = None
        self.run = None
        if re.fullmatch(r"[a-zA-Z]\w*", str_repr):
            self.name = str_repr
        else:
            halves = str_repr.split(" +: ")
            assert len(halves) == 2
            self.start = int(halves[0])
            self.run = int(halves[1])


class WhenValue():
    """Represents one value of a when statement

    An example when statement line with 4 values::

        when (!'000', _, '0101x00', '1101' to '1111') =>

    The class represents one of the following:

     * Don't care (if intialized with "_").
     * A bit-pattern (if intialized with "'0101x00'").
     * A negated bit-pattern (if intialized with "!'000'").
     * A range (if initialized with "'1101' to '1111'").

    The result of initializing with invalid input is not defined. Note that the
    range syntax is an extension not allowed in standard ASL.

    :param str_repr: The value in ASL syntax
    :type str_repr: str

    :ivar self.empty: True if the value is a don't care
    :vartype self.empty: bool or None
    :ivar self.notvalue: The bit-pattern (without the single quotes) if negated bit pattern
    :vartype self.notvalue: str or None
    :ivar self.value: The bit-pattern (without the single quotes) if bit pattern
    :vartype self.value: str or None
    :ivar self.range: The start and end (inclusive) of the range if range.
    :vartype self.range: (int, int) or None
    """

    def __init__(self, str_repr):
        self.empty = None
        self.notvalue = None
        self.value = None
        self.range = None
        if str_repr == "_":
            self.empty = True
        elif str_repr.startswith("!"):
            self.notvalue = str_repr[2:-1]
        else:
            literals = str_repr.split(" to ")
            if len(literals) == 1:
                self.value = literals[0][1:-1]
            elif len(literals) == 2:
                assert 'x' not in literals[0]
                assert 'x' not in literals[1]
                self.range = (int(literals[0][1:-1], 2), int(literals[1][1:-1], 2))
            else:
                assert False


class NopDecodeListener():
    """Defines the interface of listening to decoder file traversals

    Meant for subclassing and selectively overriding methods to visit decoder
    files.

    For nodes which have children (decode, case and when) the return value of
    the corresponding function decides whether the children should be visited or
    not. Those functions also have functions (after_listen...) that get called
    after the children have been, or would have been visited (irrespective of
    what the listen function returned). By default they return True.
    """

    def listen_decode(self, name):
        """Called on decode (`__decode decoding_name`), has children"""

        return True

    def after_listen_decode(self, name):
        """Called after visiting decode (`__decode decoding_name`)"""

        pass

    def listen_case(self, fields):
        """Called on case statements with a list of fields, has children

        For instance `case (field_name, 5 +: 2) of` would cause it to be called
        with an array of two fields.

        :param fields: A list of fields, one for each field in the case statement
        :type fields: [CaseField]
        """

        return True

    def after_listen_case(self, fields):
        """Called after visiting case"""

        pass

    def listen_when(self, values):
        """Called on when statements with a list of values, has children

        For instance `when ('xx10', _, _) of` would cause it to be called
        with an array of three values.

        :param fields: A list of values, one for each value in the when statement
        :type fields: [WhenValue]
        """

        return True

    def after_listen_when(self, values):
        """Called after visiting case"""

        pass

    def listen_field(self, name, start, run):
        """Called on field declarations (`__field fname 0 +: 5`)"""

        pass

    def listen_encoding(self, name):
        """Called on encoding (`__encoding encname`)"""

        pass

    def listen_undocumented(self):
        """Called on undocumented directives (`__UNDOCUMENTED`)"""

        pass

    def listen_unallocated(self):
        """Called on unallocated directives (`__UNALLOCATED`)"""

        pass

    def listen_unused(self):
        """Called on unused directives (`__UNUSED`)"""

        pass


class NopInstrsListener():
    """Defines the interface of listening to instruction file traversals

    Meant for subclassing and selectively overriding methods to visit
    instruction files.

    For nodes which have children (instruction and encoding) the return value of
    the corresponding function decides whether the children should be visited or
    not. Those functions also have functions (after_listen...) that get called
    after the children have been, or would have been visited (irrespective of
    what the listen function returned). By default they return True.
    """

    def listen_instruction(self, name):
        """Called on instructions (`__instruction inst_name`), has children"""

        return True

    def after_listen_instruction(self, name):
        """Called after instructions (`__instruction inst_name`)"""

        pass

    def listen_encoding(self, name):
        """Called on encoding (`__encoding enc_name`) has children"""

        return True

    def after_listen_encoding(self, name):
        """Called after encoding (`__encoding enc_name`)"""

        pass

    def listen_encode(self, code):
        """Called on encode (`__encode`), no children"""

        pass

    def listen_decode(self, code):
        """Called on decode (`__decode`), no children"""

        pass

    def listen_postencode(self, code):
        """Called on postencode (`__postencode`), no children"""

        pass

    def listen_postdecode(self, code):
        """Called on postdecode (`__postdecode`), no children"""

        pass

    def listen_execute(self, code):
        """Called on execute (`__execute`), no children"""

        pass


def visit_decoder_tree(tree, listener):
    """(Internal) Traverses the given tree of a decoder file and invokes the listener

    For each line it decides what kind of line it is and calls the corresponding
    function of the listener.

    :param tree: The syntax tree of the ASL decoder file where each node is tuple
                 of ([children], line) where children is a list of zero or more
                 child nodes and line is the line as a string stripped of all
                 whitespace and comments.
    :param listener: A listener object which implements the interface specified
                     by NopDecodeListener.
    """

    for child in tree:
        line = child[1]
        if line.startswith("__decode"):
            m = re.fullmatch(r"__decode ([a-zA-Z]\w*)", line)
            assert m
            if listener.listen_decode(m.groups()[0]):
                visit_decoder_tree(child[0], listener)
            listener.after_listen_decode(m.groups()[0])
        elif line.startswith("__field"):
            m = re.fullmatch(r"__field ([a-zA-Z]\w*) (\d+) \+: (\d+)", line)
            assert m
            groups = m.groups()
            listener.listen_field(groups[0], int(groups[1]), int(groups[2]))
        elif line.startswith("case"):
            empty_match = re.fullmatch(r"case \(\) of", line)
            fields = []
            if not empty_match:
                m = re.fullmatch(r"case \(((?:(\d+) \+: (\d+)|[a-zA-Z]\w*)(?:, (?:(\d+) \+: (\d+)|[a-zA-Z]\w*))*)\) of", line)
                assert m
                fields = m.groups()[0].split(", ")
            res_fields = []
            for field in fields:
                res_fields.append(CaseField(field))
            if listener.listen_case(res_fields):
                visit_decoder_tree(child[0], listener)
            listener.after_listen_case(res_fields)
        elif line.startswith("when"):
            m = re.match(r"when \(\) =>", line)
            vals = []
            if not m:
                m = re.match(r"when \(((?:_|!?'[01x]+'|'[01x]+' to '[01x]+')(?:, (?:_|!?'[01x]+'|'[01x]+' to '[01x]+'))*)\) =>", line)
                assert m
                vals = m.groups()[0].split(", ")
            values = []
            for value in vals:
                values.append(WhenValue(value))
            visitChildren = listener.listen_when(values)
            if visitChildren and line[m.end():] != "":
                visit_decoder_tree([([], line[m.end():].strip())], listener)
            elif visitChildren:
                visit_decoder_tree(child[0], listener)
            listener.after_listen_when(values)
        elif line.startswith("__encoding"):
            m = re.fullmatch(r"__encoding ([a-zA-Z]\w*)", line)
            assert m
            listener.listen_encoding(m.groups()[0])
        elif line == "__UNDOCUMENTED":
            listener.listen_undocumented()
        elif line == "__UNALLOCATED":
            listener.listen_unallocated()
        elif line == "__UNUSED":
            listener.listen_unused()
        else:
            print("Unexpected decoder input: :{0}:".format(line), file=sys.stderr)


def extract_code(tree, result):
    """(Internal) returns a string (split into multiple parts for efficiency) of ASL processed code extracted from the given nodes

    Processed code is asl code which contains START, END, and NEWLINE tokens
    to give it structure as opposed to indentation. This allows the code to be
    lexed using antlr lexers.

    :param tree: A list of nodes which correspond to asl code
    :type tree: [Node] where Node is ([Node], str)
    :param result: Partial results for recursion (in the top-level call this should be empty)
    :type result: [str]
    :returns: For efficiency the processed ASL code is split into pieces
    :rtype: [str]
    """

    for child in tree:
        line = child[1]
        result.append(line)
        if child[0]:
            add_start = line.startswith("if") or line.startswith("elsif") or line.startswith("else") \
                or line.startswith("case") or line.startswith("when") or line.startswith("otherwise") \
                or line.startswith("repeat") or line.startswith("while") or line.startswith("for")
            if add_start:
                result.append(" START ")
            result += extract_code(child[0], result)
            if add_start:
                result.append(" END ")
        else:
            result.append(" NEWLINE ")
    return result


def visit_instructions_listing(tree, listener):
    """(Internal) Traverses the given tree of a instructions file and invokes the listener

    For each line it decides what kind of line it is and calls the corresponding
    function of the listener.

    :param tree: The syntax tree of the ASL decoder file where each node is tuple
                 of ([children], line) where children is a list of zero or more
                 child nodes and line is the line as a string stripped of all
                 whitespace and comments.
    :param listener: A listener object which implements the interface specified
                     by NopInstrsListener.
    """

    for child in tree:
        line = child[1]
        if line == "__execute":
            code = extract_code(child[0], [])
            listener.listen_execute(" ".join(code))
        elif line.startswith("__encode"):
            code = extract_code(child[0], [])
            listener.listen_encode(" ".join(code))
        elif line.startswith("__decode"):
            code = extract_code(child[0], [])
            listener.listen_decode(" ".join(code))
        elif line.startswith("__postencode"):
            code = extract_code(child[0], [])
            listener.listen_postencode(" ".join(code))
        elif line.startswith("__postdecode"):
            code = extract_code(child[0], [])
            listener.listen_postdecode(" ".join(code))
        elif line.startswith("__encoding"):
            m = re.fullmatch(r"__encoding ([a-zA-Z]\w*)", line)
            assert m
            if listener.listen_encoding(m.groups()[0]):
                visit_instructions_listing(child[0], listener)
            listener.after_listen_encoding(m.groups()[0])
        elif line.startswith("__instruction"):
            m = re.fullmatch(r"__instruction ([a-zA-Z]\w*)", line)
            assert m
            if listener.listen_instruction(m.groups()[0]):
                visit_instructions_listing(child[0], listener)
            listener.after_listen_instruction(m.groups()[0])


def line_list(filename):
    """(Internal) Returns a list of tuples (indentation-level, line) one for every line

    Empty lines, comments and extra whitespace are striped out.
    Indents are expected to be 4 spaces.

    :param filename: Path of the asl file name (may be relative or absolute).
    :type filename: str
    :returns: List of every content line with the indentation-level as a tuple
    :rtype: [(int, str)]
    """

    decode_asl_file = open(filename, "r")
    lines = decode_asl_file.readlines()
    processed_lines = []
    for line in lines:
        assert int(line.find(line.lstrip())) % 4 == 0
        asl_indents = int(line.find(line.lstrip()) / 4)
        comment_start = line.find("//")
        if comment_start != -1:
            line = line[:comment_start]
        line = line.strip(" \t\n")
        if line != "":
            processed_lines += [(asl_indents, line)]
    return processed_lines


def tree_from_lines(lines):
    """(Internal) Generates a tree from a set of line tuples (indent-level, line)

    The following input::

        [(0, "str"), (1, "str1"), (1, str2), (0, str3)]

    would result in the tree::

        [([([], str1), ([], str2)], str), ([], str3)]

    :param lines: A list of lines where one line is the string and the indentation-level
    :type lines: [(int, str)]
    :returns: A correctly nested representation of the lines
    :rtype: [Node] where Node is ([Node], str)
    """

    tree = []
    current_stack = []
    for line in lines:
        asl_indents = line[0]
        node = ([], line[1])
        if asl_indents == 0:
            tree += [node]
            current_stack = [node]
        else:
            while len(current_stack) > asl_indents:
                current_stack = current_stack[:-1]
            current_stack[-1][0].append(node)
            current_stack += [node]
    return tree


def parse_asl_decoder_file(filename, listener):
    """Parses the given asl decoder file and invokes the listener object on each node

    :param filename: A path to the decoder file
    :type filename: str
    :param listener: A listener object which implements the same interface as NopDecodeListener
    """
    lines = line_list(filename)
    tree = tree_from_lines(lines)
    visit_decoder_tree(tree, listener)


def parse_asl_instructions_file(filename, listener):
    """Parses the given asl instruction file and invokes the listener object on each node

    :param filename: A path to the instruction file
    :type filename: str
    :param listener: A listener object which implements the same interface as NopInstrsListener
    """
    lines = line_list(filename)
    tree = tree_from_lines(lines)
    visit_instructions_listing(tree, listener)
