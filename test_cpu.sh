#!/bin/sh -e


cd chainer
python setup.py develop install

nosetests -a '!gpu' --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
