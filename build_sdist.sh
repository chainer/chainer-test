#!/bin/sh -ex

cd chainer
pip install cython
python setup.py -q sdist
