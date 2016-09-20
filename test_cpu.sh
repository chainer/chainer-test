#!/bin/sh -e


cd chainer
flake8
python setup.py develop install

nosetests -a '!gpu,!slow' --stop --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
