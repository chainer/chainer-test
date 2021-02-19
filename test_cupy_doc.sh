#!/bin/sh -ex

. ./environment.sh

pip install --user cupy/[jenkins]

cd cupy/docs

pip install --user -r requirements.txt

export SPHINXOPTS=-W

# Generate HTML and preserve it for preview.
make html
mv build/html preview

# Run doctest.
# The doctest has some bug. We need two pass doctest
make clean
make doctest
make doctest
