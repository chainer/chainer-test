#!/bin/sh -e

cd chainer
python setup.py install
pip install `chainer-cuda-requirements`

pip install nose coverage coveralls
nosetests --with-coverage --cover-branches --cover-package=chainer
coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  apt-get -y install git
  coveralls
fi
