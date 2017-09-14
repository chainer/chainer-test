#!/bin/sh -e


cd chainer
python setup.py develop install --user

export PYTHONWARNINGS="error::DeprecationWarning,ignore::FutureWarning"
nosetests --processes=4 --process-timeout=10000 -a '!gpu,!slow' --stop --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests
