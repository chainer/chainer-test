#!/bin/sh -e


cd chainer
flake8
python setup.py develop install --user

nosetests -a '!gpu,!slow' --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
