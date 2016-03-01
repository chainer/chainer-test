#!/bin/sh -ex

cd chainer
python setup.py -q develop install

cd docs
make doctest
