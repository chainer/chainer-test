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

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    --timeout=300
    --cov
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'not cudnn and not slow')
else
  pytest_opts+=(-m 'not slow')
fi

python -m pytest "${pytest_opts[@]}" tests
python ../push_coveralls.py
