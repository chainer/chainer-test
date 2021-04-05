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

cd examples

run="python -m coverage run -a --branch"

export MPLBACKEND=Agg

# K-means

$run kmeans/kmeans.py -m 1
$run kmeans/kmeans.py -m 1 --use-custom-kernel
$run kmeans/kmeans.py -m 1 -o kmeans.png


# SGEMM

$run gemm/sgemm.py

# cg

$run cg/cg.py


# cuTENSOR

$run cutensor/contraction.py
$run cutensor/elementwise_binary.py
$run cutensor/elementwise_trinary.py
$run cutensor/elementwise_reduction.py


# stream

$run stream/cublas.py
$run stream/cudnn.py
$run stream/cufft.py
$run stream/cupy_event.py
$run stream/cupy_kernel.py
$run stream/cupy_memcpy.py
$run stream/curand.py
$run stream/cusolver.py
$run stream/cusparse.py
$run stream/map_reduce.py
$run stream/thrust.py
