#!/bin/bash -e


cd chainer
python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    --timeout=60
    --cov
    --showlocals  # Show local variables on error
    -m 'not gpu and not multi_gpu and not cudnn and not slow'
)

python -m pytest "${pytest_opts[@]}" tests/chainer_tests
