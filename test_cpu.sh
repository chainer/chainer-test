#!/bin/bash -e


cd chainer
python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

export CHAINER_TEST_GPU_LIMIT=0

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
    --showlocals  # Show local variables on error
    -m 'not cudnn and not slow'
)

python -m pytest "${pytest_opts[@]}" tests/chainer_tests
