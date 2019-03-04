#!/bin/sh -ex

cd cupy
python setup.py -q build -j 4 develop install --user || python setup.py -q develop install --user

cd docs
export SPHINXOPTS=-W

# Generate HTML and preserve it for preview.
make html
mv build/html preview

# Run doctest.
# The doctest has some bug. We need two pass doctest
make clean
make doctest
make doctest
