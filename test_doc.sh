#!/bin/sh -ex

cd chainer
python setup.py -q develop install

cd docs
pip install sphinx
make doctest
