#!/bin/sh -ex

timeout 20m pip install -vvvv chainer/dist/*.tar.gz --user

# check if cupy is installed
python -c 'import cupy'
