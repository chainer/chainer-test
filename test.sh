#!/bin/sh -ex

cd chainer
python setup.py -q install
python cuda_deps/setup.py -q install

pip install -q nose coverage coveralls
nosetests --with-coverage --cover-branches --cover-package=chainer
coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  coveralls
fi
