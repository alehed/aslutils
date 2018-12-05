import re
import sys


class CaseField():

    def __init__(self, str_repr):
        self.name = None
        self.start = None
        self.run = None
        if re.fullmatch(r"[a-zA-Z]\w*", str_repr):
            self.name = str_repr
        else:
            halves = str_repr.split(" +: ")
            self.start = int(halves[0])
            self.run = int(halves[1])


class WhenValue():

    def __init__(self, str_repr):
        self.empty = None
        self.notvalue = None
        self.value = None
        self.values = None
        if str_repr == "_":
            self.empty = True
        elif str_repr.startswith("!"):
            self.notvalue = str_repr[2:-1]
        else:
            literals = str_repr.split(" to ")
            if len(literals) == 1:
                self.value = literals[0][1:-1]
            elif len(literals) == 2:
                self.values = [literals[0][1:-1], literals[1][1:-1]]
            else:
                assert False


class NopDecodeListener():

    def listen_decode(self, name):
        return True

    def listen_field(self, name, start, run):
        pass

    def listen_case(self, fields):
        return True

    def listen_when(self, values):
        return True

    def listen_encoding(self, name):
        pass

    def listen_undocumented(self):
        return True

    def listen_unallocated(self):
        pass

    def listen_unused(self):
        pass

    def after_listen_decode(self, name):
        pass

    def after_listen_case(self, fields):
        pass

    def after_listen_when(self, values):
        pass


class NopInstrsListener():

    def listen_instruction(self, name):
        return True

    def listen_encoding(self, name):
        return True

    def listen_encode(self, code):
        pass

    def listen_decode(self, code):
        pass

    def listen_postencode(self, code):
        pass

    def listen_postdecode(self, code):
        pass

    def listen_execute(self, code):
        pass

    def after_listen_instruction(self, name):
        pass

    def after_listen_encoding(self, name):
        pass


def visit_decoder_tree(tree, listener):
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


# returns a list of tuples (indentation, line)
def line_list(file):
    decode_asl_file = open(file, "r")
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


# A node is ([children], line)
def tree_from_lines(lines):
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


def parse_asl_decoder_file(name, listener):
    lines = line_list(name)
    tree = tree_from_lines(lines)
    visit_decoder_tree(tree, listener)


def parse_asl_instructions_file(name, listener):
    lines = line_list(name)
    tree = tree_from_lines(lines)
    visit_instructions_listing(tree, listener)
