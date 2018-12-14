Tutorial
========

From a user perspective the interesting modules are :mod:`parse_asl_file`
which exports functionality to parse the different kinds of asl files and the
:mod:`asl2c` which exports a function (:func:`asl_to_c`) that can convert
pseudocode ASL to C code. In this short tutorial we will look at how to
integrate both modules in order to produce an c interpreter for the instruction
set discussed in the introduction section.

For reference, the decoder file is:

.. literalinclude:: example/arithmetic-decoder.asl

and the instruction file is:

.. literalinclude:: example/arithmetic-instrs.asl

At first we will parse the instruction file in order to get the decode and
execute code associated with each instruction. All we have to do here is
fill two maps, one that maps from encoding name to decoder code, the other that
maps from encoding name to execute code. Usually what you want to do there is
just save the ASL code and transform it later once the context and the available
variable names are known, but here the example so simple that we can do the
transformation right in the listener of the instruction file.

In order to get the c code from the ASL, we will use the :func:`asl_to_c`
function.

The instruction listener would probably look something like this:

.. literalinclude:: example/parse-arithmetic.py
    :linenos:
    :language: python
    :lines: 9-39

As documented, asl_to_c returns an array of c code lines which we store in the
corresponding map. In case of :func:`listen_decode` some of the variables might
be initialized to constants and therefor don't appear in the C code. Those
variables need to be added manually to the code. Here we pull a shortcut
assuming all variables are of type integer.

Now, all that is left is to parse the decoder using another listener and
generating code this time.

The decoder listener looks something like this:

.. literalinclude:: example/parse-arithmetic.py
    :linenos:
    :language: python
    :lines: 42-86

This leaves us with the code that puts all the pieces together. In essence this
generates a static prefix and a suffix, between which the generated code is
emitted. Note that the generated code is quite unreadable as it doesn't use
indentation. By looking at the depth of the field stack, the appropriate amount
of indentation can be inferred.

It would probably look something like this:

.. literalinclude:: example/parse-arithmetic.py
    :linenos:
    :language: python
    :lines: 89-111

Despite taking some shortcuts here and there, we have seen a complete example of
generating an interpreter for the small instruction set. The generated code will
print out 0xFF.
