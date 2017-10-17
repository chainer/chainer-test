#!/bin/sh -e


cd chainer
python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

python -m pytest --timeout=60 --cov -m 'not gpu and not multi_gpu and not slow' tests/chainer-tests
