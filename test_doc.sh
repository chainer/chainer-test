#!/bin/sh -ex

cd cupy
python setup.py -q build -j 4 develop install --user || python setup.py -q develop install --user
cd ..

cd chainer
python setup.py -q build -j 4 develop install --user || python setup.py -q develop install --user

python -m pip install matplotlib --user

cd docs
make html
make clean
# The doctest has some bug. We need two pass doctest
make doctest
make doctest
