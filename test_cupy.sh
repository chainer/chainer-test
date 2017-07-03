#!/bin/sh -ex

cd cupy
flake8
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export PYTHONWARNINGS="ignore::FutureWarning"

if [ $CUDNN = none ]; then
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=cupy -a '!cudnn,!slow'
else
  nosetests --processes=4 --process-timeout=10000 --stop --with-coverage --cover-branches --cover-package=cupy -a '!slow'
fi

coverage xml -i

if [ $COVERALLS_REPO_TOKEN ]; then
  python ../push_coveralls.py
fi
