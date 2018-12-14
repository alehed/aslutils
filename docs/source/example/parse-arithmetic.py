from aslutils.parse_asl_file import NopInstrsListener
from aslutils.parse_asl_file import NopDecodeListener
from aslutils.parse_asl_file import parse_asl_decoder_file
from aslutils.parse_asl_file import parse_asl_instructions_file
from aslutils.asl2c import asl_to_c
from aslutils.asl_type import ASLType


class InstrListener(NopInstrsListener):

    def __init__(self):
        self.encodings = []
        self.decode_map = {}
        self.execute_map = {}

    def listen_instruction(self, name):
        self.encodings = []
        return True

    def listen_encoding(self, name):
        self.encodings.append(name)
        return True

    def listen_decode(self, code):
        vars, c_code = asl_to_c(code, [])
        decls = []
        for varname, var in vars.items():
            if not var[0] and var[1] is not None and var[2] is not None:
                if var[1].type == ASLType.Kind.int:
                    decls.append("int64_t {0} = {1};"
                                 .format(varname, var[2]))
        c_code = decls + c_code
        self.decode_map[self.encodings[-1]] = c_code

    def listen_execute(self, code):
        # Here we don't expect any declarations
        c_code = asl_to_c(code, [("result", 64)])[1]
        for encoding in self.encodings:
            self.execute_map[encoding] = c_code


class DecoderListener(NopDecodeListener):

    def __init__(self, decodemap, executemap):
        self.decode_map = decodemap
        self.execute_map = executemap
        self.fields_stack = []

    def listen_case(self, fields):
        self.fields_stack.append([f.name if f.name
                                  else "((word >> {0}) & ((1 << {1}) - 1))"
                                  .format(f.start, f.run)
                                  for f in fields])
        return True

    def after_listen_case(self, fields):
        print('{\nassert(0);\n}')
        self.fields_stack.pop()

    def listen_when(self, values):
        components = []
        for i, value in enumerate(values):
            if value.value is not None:
                components.append("{0} == {1}"
                                  .format(self.fields_stack[-1][i],
                                          int(value.value, 2)))

        if not components:
            print("if (1) {")
        else:
            print("if (({0})) {{".format(") && (".join(components)))
        return True

    def after_listen_when(self, values):
        print("} else")

    def listen_field(self, name, start, run):
        print("u_int64_t {0} = (word >> {1}) & ((1 << {2}) - 1);"
              .format(name, start, run))

    def listen_encoding(self, name):
        print("\n".join(self.decode_map[name]))
        print("\n".join(self.execute_map[name]))

    def listen_unused(self):
        print('assert(0);')


prefix = """#include <stdio.h>
#include <sys/types.h>
#include <assert.h>

#define UInt(num) ((u_int64_t)num)

int main() {
int64_t result;
u_int32_t word = 0x80FE0000;
"""
print(prefix)

l1 = InstrListener()
parse_asl_instructions_file('arithmetic-instrs.asl', l1)

l2 = DecoderListener(l1.decode_map, l1.execute_map)
parse_asl_decoder_file('arithmetic-decoder.asl', l2)

suffix = """printf("0x%lx\\n", result);
return 0;
}
"""
print(suffix)
