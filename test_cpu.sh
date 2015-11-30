#!/bin/sh -e

pip install -U pip

cd chainer
python setup.py develop
python setup.py install

pip install nose mock coverage
nosetests -a '!gpu' --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
