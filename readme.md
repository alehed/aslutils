# AslUtils

Utility scripts to parse ASL files and the actual ASL language.

## Installing

Preferably this is installed in a virtual environment. To create a virtual environment in the current directory write `python3 -m venv env/`. To enter the virtual environment use `source env/bin/activate`.

To install simply use pip: `pip3 install aslutils`.

### Installing for development

To install the package for development, clone it and then install it in editable mode: `pip3 install -e /path/to/aslutils/` (i.e. the directory that contains setup.py).

## Using aslutils

The documentation can be found at <https://alehed.github.io/aslutils/>

## Developing

### Generating the documentation

`aslutils` uses sphinx (`pip install sphinx`) to generate the documentation. From the root folder the command to generate the html documentation is `sphinx-build -b html docs/source docs/build`. The docs can then be found at `docs/build/index.html`.

If anything in the source changes (class names, new classes etc.) the aslutils.rst and modules.rst files have to be regenerated. This can be done via `sphinx-apidoc -f -o docs/source/ aslutils`. Do not edit those files manually as the changes will be overwritten once sphinx-apidoc is rerun.

### Build time dependencies

In order to build the project locally, you need to have `antlr4` (<https://www.antlr.org/>) and the corresponding antlr4 python runtime installed (`pip install antlr4-python3-runtime==4.?.?`, the version has to match the installed antlr version).

### Building the parser

The ASL visitor code is generated with `antlr4 -Dlanguage=Python3 -no-listener -visitor ./aslutils/ASL.g4`. This has to be done every time the file ASL.g4 is changed.

### Packaging

Note: I am currently the sole packager of this project, so this section is only for reference to my later self.

Once antlr is installed, this step is easy. The dependencies for packaging are: wheel, setuptools and twine (`pip install wheel setuptools twine`)

After old versions are removed from the dist directory `rm dist/*`, the package needs to be generated with: `python setup.py sdist bdist_wheel --universal`. Then it can be uploaded using twine: `twine upload dist/*`.

#### Release process

Again, this is only for myself.

 1. Decide to do a new release
 1. Fully regenerate the documentation and commit the changes
 1. Bump the version in setup.py and commit
 1. Tag the latest commit and push it
 1. Publish the documentation with the provided script
 1. Do the steps described in packaging
