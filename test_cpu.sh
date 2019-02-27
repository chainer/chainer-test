#!/bin/bash -e


cd chainer
python setup.py develop install --user

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

export CHAINER_TEST_GPU_LIMIT=0

export OMP_NUM_THREADS=1

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
    --cov-report=
    --cov-append
    --showlocals  # Show local variables on error
)

pytest_marks=(
    not cudnn and not slow
)

if [ $IDEEP = none ]; then
  pytest_marks+=(and not ideep)
fi

pytest_opts+=(-m "${pytest_marks[*]}")

find tests/chainer_tests -name "test_*.py" -type f|xargs -L 10 python -m pytest "${pytest_opts[@]}"
