#!/bin/sh -ex

cd chainer/docs
pip install sphinx
make doctest
cd ../..
