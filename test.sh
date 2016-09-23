#!/bin/sh -ex

cd chainer
flake8
python setup.py develop install --user

if [ $CUDNN = none ]; then
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=chainer,cupy -a '!cudnn,!slow'
else
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=chainer,cupy -a '!slow'
fi

coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  coveralls
fi
