#!/bin/sh -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'slow and not cudnn')
else
  pytest_opts+=(-m 'slow')
fi

python -m pytest "${pytest_opts[@]}" tests
