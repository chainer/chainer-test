#!/bin/bash -ex

# Chainer setup script installs specific version of CuPy.
# We need to install Chainer first for test.
cd chainer
python setup.py install --user
cd ..

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user
cd ..

cd chainer

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

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
    slow
)

if [ $CUDNN = none ]; then
  pytest_marks+=(and not cudnn)
fi

if [ $IDEEP = none ]; then
  pytest_marks+=(and not ideep)
fi

pytest_opts+=(-m "${pytest_marks[*]}")

find tests/chainer_tests -name "test_*.py" -type f|xargs -L 10 python -m pytest "${pytest_opts[@]}"
