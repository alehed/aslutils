import setuptools

import re
import subprocess
import sys

# Find antlr version for runtime dep
antlr_version = ""
try:
    antlr = subprocess.run(["antlr4"], stdout=subprocess.PIPE)
    if antlr.returncode != 0:
        print("Could not find antlr4 installation. Unable to proceed", file=sys.stderr)
        exit(1)
    print(antlr.stdout.decode("utf-8"))
    match = re.match(r"ANTLR Parser Generator  Version 4\.(\d+)\.", antlr.stdout.decode("utf-8"))
    assert match
    antlr_version = "==4." + match.groups()[0] + ".*"
except OSError as e:
    print("Execution failed:", e, file=sys.stderr)
    exit(1)

# Run Antrl
try:
    antlr = subprocess.run(["antlr4", "-Dlanguage=Python3", "-no-listener", "-visitor", "./aslutils/ASL.g4"], stdout=subprocess.PIPE)
    if antlr.returncode != 0:
        print("Could not run antlr4. Unable to proceed", file=sys.stderr)
        exit(1)
except OSError as e:
    print("Execution failed:", e, file=sys.stderr)
    exit(1)


with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aslutils",
    version="0.0.2",
    author="Alexander Hedges",
    author_email="ahedges@ethz.ch",
    description="Code to parse Arm Specification Language (ASL) files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alehed/aslutils.git",
    packages=setuptools.find_packages(),
    install_requires=['antlr4-python3-runtime{0}'.format(antlr_version)],
    python_requires='>=3',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
