__decode arithmetic
    case (30 +: 2) of
        when ('00') => __UNUSED
        when ('01') =>
            __field op 29 +: 2
            __field operand1 8 +: 8
            __field operand2 0 +: 8
            case (op, operand1, operand2) of
                when ('10', _, _) => __encoding subtract
                when ('11', _, _) => __encoding add
        when ('10') =>
            __field op 24 +: 8
            __field operand 16 +: 8
            case () of
                when () => __encoding increment
        when ('11') => __UNUSED
