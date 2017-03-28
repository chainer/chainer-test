#!/bin/sh -e


cd chainer
flake8
python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"
nosetests --processes=4 --process-timeout=10000 -a '!gpu,!slow' --stop --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
