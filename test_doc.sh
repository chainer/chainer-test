#!/bin/sh -ex

cd chainer
python setup.py -q develop install --user

cd docs
make doctest
