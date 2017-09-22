#!/bin/sh -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"

if [ $CUDNN = none ]; then
  nosetests --with-coverage --cover-branches --cover-package=cupy -a '!cudnn,!slow' tests
else
  nosetests --with-coverage --cover-branches --cover-package=cupy -a '!slow' tests
fi

python ../push_coveralls.py
