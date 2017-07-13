#!/bin/sh -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user
cd ..

cd chainer
python setup.py install --user

export PYTHONWARNINGS="ignore::FutureWarning"

if [ $CUDNN = none ]; then
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=chainer -a '!cudnn,!slow'
else
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=chainer -a '!slow'
fi

python ../push_coveralls.py
