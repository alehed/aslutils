__instruction addition
    __encoding add
        __decode
            integer op1 = UInt(operand1);
            integer op2 = UInt(operand2);

    __encoding increment
        __decode
            integer op1 = UInt(operand);
            integer op2 = 1;

    __execute
        integer result = op1 + op2;

__instruction subtraction
    __encoding subtract
        __decode
            integer op1 = UInt(operand1);
            integer op2 = UInt(operand2);

    __execute
        integer result = op1 - op2;
