#!/bin/bash -ex

. ./environment.sh

pip install --user -e cupy/

cd cupy

# Shows cupy config before running the tests
python -c 'import cupy; cupy.show_config()'

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    -rfEX
    --timeout=300
    --junit-xml=result.xml
    --cov
    --no-cov-on-fail
    --showlocals  # Show local variables on error
)

if [ $CUDNN = none ]; then
  pytest_opts+=(-m 'not cudnn and not slow')
else
  pytest_opts+=(-m 'not slow')
fi

python -m pytest "${pytest_opts[@]}" tests

# Submit coverage to Coveralls
python ../push_coveralls.py

# Submit coverage to Codecov
# Codecov uses `coverage.xml` generated from `.coverage`
coverage xml
codecov

# Run benchmark on Python 3
if [ "$(python -c 'import sys; print(sys.version_info.major)')" = "3" ]; then
  rm -rf cupy-perf
  git clone https://github.com/niboshi/cupy-perf.git cupy-perf
  pushd cupy-perf
  python run.py --show-gpu
  popd
fi
