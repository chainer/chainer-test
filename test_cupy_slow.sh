#!/bin/bash -ex

. ./environment.sh

pip install --user cupy/[jenkins]

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    -rfEX
    --timeout=300
    --junit-xml=result.xml
    --cov
    --no-cov-on-fail
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'slow and not cudnn')
else
  pytest_opts+=(-m 'slow')
fi

pushd cupy
python -m pytest "${pytest_opts[@]}" tests/install_tests
popd

pushd cupy/tests
python -m pytest "${pytest_opts[@]}" cupy_tests cupyx_tests example_tests
popd
