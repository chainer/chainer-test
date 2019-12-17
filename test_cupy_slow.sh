#!/bin/bash -ex

pip install --user -e cupy/

cd cupy

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    -rfEX
    --timeout=300
    --junit-xml=result.xml
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'slow and not cudnn')
else
  pytest_opts+=(-m 'slow')
fi

python -m pytest "${pytest_opts[@]}" tests
