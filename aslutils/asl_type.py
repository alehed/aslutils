from enum import Enum


class ASLType():
    """Type information for an ASL expression

    Currently the following types are supported (see enum ASLType.Kind):
     * bits -- bitstring of length n
     * bitpattern -- bitstring of length n which may contain don't care bits (x)
     * int -- mathematical integer with (in theory) infinite precision
     * bool -- either true or false
     * real -- mathematical real number with (in theory) infinite precision
     * other -- custom types

    :param type: enum value of type ASLType.Kind
    :type type: ASLType.Kind
    :param value: for bits and bitpatterns this specifies the length if known,
                  for other it specifies the type name (opt)
    """

    class Kind(Enum):
        bits = 1
        bitpattern = 2
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
        """Returns type in C (as a str) that corresponds the closest to self"""

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
