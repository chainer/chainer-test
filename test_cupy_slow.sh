#!/bin/sh -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

if [ $CUDNN = none ]; then
  python -m pytest --cov -m 'slow and not cudnn' tests
else
  python -m pytest --cov -m 'slow' tests
fi
