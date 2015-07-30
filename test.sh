#!/bin/sh -ex

cd chainer
python setup.py -q install

if [ -e cuda_deps/setup.py ]; then
  python cuda_deps/setup.py -q install
fi

pip install -q nose mock coverage coveralls

if [ -d cupy ]; then
  nosetests --processes=12 --process-timeout=10000 --with-coverage --cover-branches --cover-package=cupy tests/cupy_tests
  nosetests --with-coverage --cover-branches --cover-package=chainer tests/chainer_tests
else
  nosetests --with-coverage --cover-branches --cover-package=chainer
fi

coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  coveralls
fi
