#!/bin/bash -e


pip install --user -e chainer/[jenkins]
# It's not possible to install only requirements.
# Chainer is uninstalled after the installation.
# TODO(niboshi): Use other installation tool
# (https://github.com/chainer/chainer/issues/5862)
pip uninstall -y chainer

pip install --user -e chainer/

cd chainer

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

export CHAINER_TEST_GPU_LIMIT=0

export OMP_NUM_THREADS=1

pytest_opts=(
    -rfEX
    --timeout=300
    --junit-xml=result.xml
    --cov
    --no-cov-on-fail
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
