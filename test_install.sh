#!/bin/sh -ex

pip install $DEPENDENCY

pip install -vvvv chainer/dist/*.tar.gz
