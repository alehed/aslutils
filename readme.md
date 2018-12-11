# AslUtils

Utility scripts to parse ASL files and the actual ASL language.

## Installing

Preferably this is installed in a virtual environment. To create a virtual environment in the current directory write `python3 -m venv env/`. To enter the virtual environment use `source env/bin/activate`.

To install simply use pip: `pip3 install aslutils`.

## Using aslutils

The documentation can be found

## Developing

### Generating the documentation

`aslutils` uses sphinx (`pip install sphinx`) to generate the documentation. From the root folder the command to generate the html documentation is `sphinx-build -b html docs/source docs/build`. The docs can then be found at `docs/build/index.html`.

### Build time dependencies

In order to build the project locally, you need to have `antlr4` (<https://www.antlr.org/>) and the corresponding antlr4 python runtime installed (`pip install antlr4-python3-runtime==4.?.?`, the version has to match the installed antlr version).

### Building the parser

The ASL visitor code is generated with `antlr4 -Dlanguage=Python3 -no-listener -visitor ./aslutils/ASL.g4`.

### Packaging

Note: I am currently the sole packager of this project, so this section is only for reference to my later self.

Once antlr is installed, this step is easy.

First the package needs to be generated with: `python setup.py bdist_wheel --universal`. Then the package can be uploaded using twine (`pip install twine`): `twine upload dist/*`.
