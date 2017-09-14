#!/bin/sh -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user
cd ..

cd chainer
python setup.py install --user

export PYTHONWARNINGS="error::DeprecationWarning,ignore::FutureWarning"

if [ $CUDNN = none ]; then
  nosetests --stop --with-coverage --cover-branches --cover-package=chainer -a '!cudnn,!slow' tests
else
  nosetests --stop --with-coverage --cover-branches --cover-package=chainer -a '!slow' tests
fi

python ../push_coveralls.py
