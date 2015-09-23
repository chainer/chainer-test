#!/bin/sh -ex

cd chainer
python setup.py -q install

cd docs
pip install sphinx
make doctest
