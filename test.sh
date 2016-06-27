#!/bin/sh -ex

cd chainer
python setup.py develop install

if [ $CUDNN = none ]; then
  nosetests --processes=4 --process-timeout=10000 --with-coverage --cover-branches --cover-package=chainer,cupy -a '!cudnn' -v
else
  nosetests --processes=4 --process-timeout=10000 --with-coverage --cover-branches --cover-package=chainer,cupy -v
fi

flake8
coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  coveralls
fi
