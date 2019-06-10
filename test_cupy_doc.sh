#!/bin/sh -ex

pip install --user -e cupy/

cd cupy/docs

export SPHINXOPTS=-W

# Generate HTML and preserve it for preview.
make html
mv build/html preview

# Run doctest.
# The doctest has some bug. We need two pass doctest
make clean
make doctest
make doctest
