#!/bin/sh -ex

. ./environment.sh

pip install -U pip --user

cd cupy
rm -rf dist
python setup.py -q sdist
cd dist
pip install *.tar.gz --user
cd ..

python -m pip install coverage matplotlib --user

run="python -m coverage run -a --branch"

export MPLBACKEND=Agg

# K-means

$run examples/kmeans/kmeans.py -m 1
$run examples/kmeans/kmeans.py -m 1 --use-custom-kernel
$run examples/kmeans/kmeans.py -m 1 -o kmeans.png


# SGEMM

if [ -f examples/gemm/sgemm.py ]; then
  $run examples/gemm/sgemm.py
fi

