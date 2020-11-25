#!/bin/bash -ex

. ./environment.sh

pip install --user -e chainer/[jenkins]
# It's not possible to install only requirements.
# Chainer is uninstalled after the installation.
# TODO(niboshi): Use other installation tool
# (https://github.com/chainer/chainer/issues/5862)
pip uninstall -y chainer

# Chainer setup script installs specific version of CuPy.
# We need to install Chainer first for test.
pip install --user -e chainer/

pip install --user -e cupy/

cd chainer

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

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
    slow
)

if [ $CUDNN = none ]; then
  pytest_marks+=(and not cudnn)
fi

if [ $IDEEP = none ]; then
  pytest_marks+=(and not ideep)
fi

pytest_opts+=(-m "${pytest_marks[*]}")

python -m pytest "${pytest_opts[@]}" tests/chainer_tests
