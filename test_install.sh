#!/bin/sh -ex

pip install $DEPENDENCY

timeout 20m pip install -vvvv chainer/dist/*.tar.gz
