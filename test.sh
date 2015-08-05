#!/bin/sh -ex

cd chainer
python setup.py -q install

if [ -e cuda_deps/setup.py ]; then
  python cuda_deps/setup.py -q install
fi

pip install -q nose mock coverage coveralls
nosetests --with-coverage --cover-branches --cover-package=chainer
coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  coveralls
fi
