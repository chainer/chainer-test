#!/bin/sh -e

cd chainer
python setup.py build
python setup.py install

pip install nose mock coverage
nosetests -a '!gpu' --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests

coverage xml -i
