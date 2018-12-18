#!/bin/bash -ex

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user

export CUPY_DUMP_CUDA_SOURCE_ON_ERROR=1

pytest_opts=(
    --timeout=300
    --junit-xml=result.xml
    --cov
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

# Run benchmark
rm -rf cupy-perf
git clone https://github.com/niboshi/cupy-perf.git cupy-perf
pushd cupy-perf
python run.py --show-gpu
popd
