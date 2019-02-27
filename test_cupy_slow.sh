#!/bin/bash -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
    --cov-report=
    --cov-append
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'slow and not cudnn')
else
  pytest_opts+=(-m 'slow')
fi

find tests -name "test_*.py" -type f|xargs -L 10 python -m pytest "${pytest_opts[@]}"
