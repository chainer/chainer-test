#!/bin/bash -e


cd chainer
python setup.py develop install --user

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

export CHAINER_TEST_GPU_LIMIT=0

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
    --showlocals  # Show local variables on error
)

pytest_marks=(
    not cudnn and not slow
)

if [ $IDEEP = none ]; then
  pytest_marks+=(and not ideep)
fi

pytest_opts+=(-m "${pytest_marks[*]}")

python -m pytest "${pytest_opts[@]}" tests/chainer_tests
