Introduction
============

What is ASL?
------------

ASL stands for ARM Specification Language. When the ARM instruction set
specification was released in machine readable format they also released tools
to parse it and generate files in an intermediate language (think XML, but more
readable) that is very succinct and easy to understand. This language, called
ASL, happens to be a superset of the language they already use for the
pseudocode that describes what the individual instructions do. Confusingly, the
pseudocode language will also be referred to as ASL (sometimes it is also
referred to as "pseudocode ASL" or simply pseudocode).

The structure of ASL is quite similar to python in that it uses indentation to
to structure the code.

In order to be useful the ASL file can have different structures.

Decoder files
~~~~~~~~~~~~~

For instance there is the decoder asl file which describes the decoding tree of
an instruction. The top level directive of a decoding tree is `__decode` which
specifies the "instruction set". Inside of that there are nested case
statements (each with a couple of when cases) which cover all the possible
encodings. In the last leaf when statements it is either specified that the
encoding is invalid or what the encoding is called.

Instruction files
~~~~~~~~~~~~~~~~~

Another type of asl file is an instruction file where all the encodings are
described in more detail. For instance each encoding can have associated
pseudocode for encoding and decoding. Also encodings can be grouped into
instructions which share pseudocode for encoding/decoding and pseudocode that
describes the execution of the instruction.

For examples of how these files look, please take a look at the next section.

Example files
-------------

Lets look a at simple example of an encoding for three instructions:

 * add (opcode: 01100000)
 * increment (opcode: 10000000)
 * subtract (opcode: 01000000)

We are decoding a four byte word. Increment takes the second byte as an operand.
Add and subtract take the last two bytes as operands.

The example decoder file would look like this::

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
                field operand 16 +: 8
                case () of
                    when () => __encoding increment
            when ('11') => __UNUSED

Since increment and add some functionality they can be grouped together in the
instruction file.

For our hypoghetical instruction set the instructions file would look something
like::
    
    __instruction addition
        __encoding add
            __decode
                integer op1 = UInt(operand1);
                integer op2 = UInt(operand2);

        __encoding increment
            __decode
                integer op1 = UInt(op);
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

Processed ASL
-------------

Python-like indentation cannot be described by context-free grammars. This seems
to be a problem since context-free grammars are the tool for the job to describe
programming languages. Fortunately, python-like indentation can be turned into
something that allows description via context-free grammars via a pre-processing
step. This step inserts extra "BEGIN" and "END" tokens every time the
indentation is increased or decreased respectively. Additionally for easier
handling newlines are replaced with a NEWLINE token. ASL that has been
pre-processed in this way is referred to "processed ASL" in the documentation.
