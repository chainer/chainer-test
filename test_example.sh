#!/bin/sh -ex

pip install -U pip

cd chainer
rm -rf dist
python setup.py -q sdist
cd dist
pip install *.tar.gz
cd ..

if [ -e cuda_deps/setup.py ]; then
  python cuda_deps/setup.py -q install
fi

if apt-get --version; then
  apt-get install -y libjpeg-dev zlib1g-dev
elif yum --version; then
  yum -y install libjpeg-devel zlib-devel
else
  echo "both apt-get and yum command are not found"
  exit 1
fi
pip install coverage pillow

run="coverage run -a --branch"

# mnist
echo "Running mnist example"

# change epoch
$run examples/mnist/train_mnist.py --epoch=1 --unit=10
$run examples/mnist/train_mnist.py --gpu=0 --epoch=1 --unit=10
$run examples/mnist/train_mnist.py --net=parallel --epoch=1 --unit=10

# ptb
echo "Running ptb example"

$run examples/ptb/download.py
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
$run examples/imagenet/compute_mean.py -r ../data/imagenet $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a nin -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a alex -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a alexbn -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a googlenet -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py --test -a googlenetbn -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data

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

# show coverage
coverage report -m --include="examples/*"
coverage xml --include="examples/*"
