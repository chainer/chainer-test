#!/bin/sh -e


cd chainer
python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

nosetests --processes=4 --process-timeout=10000 -a '!gpu,!slow' --stop --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests
