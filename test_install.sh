#!/bin/sh -ex

timeout 20m pip install -vvvv chainer/dist/*.tar.gz --user

# check if cupy is installed
if [ $CUDNN = none ]; then
  python -c 'import cupy'
else
  python -c 'import cupy.cuda.cudnn; print(cupy.cuda.cudnn.getVersion())'
fi
