import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aslutils",
    version="0.0.1",
    author="Alexander Hedges",
    author_email="ahedges@ethz.ch",
    description="Code to parse Arm Specification Language (ASL) files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://code.systems.ethz.ch/diffusion/ASLUTIL/aslutils.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
