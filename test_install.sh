#!/bin/sh -ex

. ./environment.sh

timeout 20m pip install -vvvv chainer/dist/*.tar.gz --user

python -c 'import chainer'
