#!/bin/sh -ex

PREV_VER=2.0.0
CHAINER_DIR=chainer-${PREV_VER}

pip install -U pip --user

cd cupy
python setup.py build -j 4 develop install --user || python setup.py develop install --user
cd ..

cd chainer
rm -rf dist
python setup.py -q sdist
cd dist
pip install *.tar.gz --user
cd ..

python -m pip install coverage matplotlib --user
python -m pip install olefile --user
python -m pip install --global-option="build_ext" --global-option="--disable-jpeg" pillow --user

run="coverage run -a --branch"

export MPLBACKEND=Agg

export OMP_NUM_THREADS=1

cd ..
curl -L -o v${PREV_VER}.tar.gz https://github.com/pfnet/chainer/archive/v${PREV_VER}.tar.gz
tar xzf v${PREV_VER}.tar.gz
cd ${CHAINER_DIR}

# mnist
echo "Running mnist example"

# change epoch
$run examples/mnist/train_mnist.py --epoch=1 --unit=10
$run examples/mnist/train_mnist.py --gpu=0 --epoch=1 --unit=10
$run examples/mnist/train_mnist_model_parallel.py --gpu0=0 --gpu1=1 --epoch=1 --unit=10
$run examples/mnist/train_mnist_data_parallel.py --gpu0=0 --gpu1=1 --epoch=1 --unit=10

# ptb
echo "Running ptb example"

$run examples/ptb/train_ptb.py --epoch=1 --unit=10 --test
$run examples/ptb/train_ptb.py --gpu=0 --epoch=1 --unit=10 --test

# sentiment
echo "Running sentiment example"

$run examples/sentiment/download.py
$run examples/sentiment/train_sentiment.py --epoch=1 --batchsize=1 --epocheval=1 --test
$run examples/sentiment/train_sentiment.py --gpu=0 --epoch=1 --batchsize=1 --epocheval=1 --test 

# imagenet
echo "Runnig imagenet example"

imagenet_data=../data/imagenet/data.txt
$run examples/imagenet/compute_mean.py -R ../data/imagenet $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a nin -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a alex -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a googlenet -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a googlenetbn -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data

# word2vec
echo "Running word2vec example"

# note that ptb.train.txt is already downloaded

$run examples/word2vec/train_word2vec.py -e 1 -b 10 --test
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --gpu=0 --test
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 -m cbow --out-type ns --test
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 -m cbow --out-type ns --gpu=0 --test
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --out-type original --test
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --out-type original --gpu=0 --test
echo "it" | $run examples/word2vec/search.py

# vae
echo "Runnig VAE example"

$run examples/vae/train_vae.py -e 1 --test
$run examples/vae/train_vae.py -e 1 --gpu=0 --test

# dcgan
echo "Runnig DCGAN example"

$run examples/dcgan/train_dcgan.py -b 1 -e 1 -i ../data/dcgan --n_hidden=10 --snapshot_interval 1 --display_interval 1
$run examples/dcgan/train_dcgan.py -b 1 -e 1 --gpu=0 -i ../data/dcgan --n_hidden=10 --snapshot_interval 1 --display_interval 1

# show coverage
coverage report -m --include="examples/*"
coverage xml --include="examples/*"
