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


# cg

$run examples/cg/cg.py


# cuTENSOR

$run examples/cutensor/contraction.py
$run examples/cutensor/elementwise_binary.py
$run examples/cutensor/elementwise_trinary.py
$run examples/cutensor/elementwise_reduction.py


# stream

$run examples/stream/cublas.py
$run examples/stream/cudnn.py
$run examples/stream/cufft.py
$run examples/stream/cupy_event.py
$run examples/stream/cupy_kernel.py
$run examples/stream/cupy_memcpy.py
$run examples/stream/curand.py
$run examples/stream/cusolver.py
$run examples/stream/cusparse.py
$run examples/stream/map_reduce.py
$run examples/stream/thrust.py
