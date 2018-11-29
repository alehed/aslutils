from enum import Enum


class ASLType():
    class Kind(Enum):
        bits = 1
        bitmask = 2
        int = 3
        bool = 4
        real = 5
        other = 6

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def __eq__(self, other):
        if type(other) == ASLType:
            return self.type == other.type
        elif type(other) == ASLType.Kind:
            return self.type == other
        else:
            return False

    def c_type(self):
        if self.type == self.Kind.bits:
            return "u_int64_t"
        elif self.type == self.Kind.int:
            return "int64_t"
        elif self.type == self.Kind.bool:
            return "bool"
        elif self.type == self.Kind.real:
            return "double"
        elif self.type == self.Kind.other:
            return "const char*"
        else:
            assert False
            return None
