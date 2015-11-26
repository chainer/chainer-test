#!/bin/sh -ex

cd chainer
rm -rf dist
python setup.py -q sdist
cd dist
pip install *.tar.gz
cd ..

if [ -e cuda_deps/setup.py ]; then
  python cuda_deps/setup.py -q install
fi

if which apt-get; then
  apt-get install -y libjpeg-dev zlib1g-dev
elif which yum; then
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
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" examples/mnist/train_mnist.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" examples/mnist/train_mnist.py

$run examples/mnist/train_mnist.py
$run examples/mnist/train_mnist.py --gpu=0
$run examples/mnist/train_mnist.py --net=parallel

# ptb
echo "Running ptb example"

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" examples/ptb/train_ptb.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" examples/ptb/train_ptb.py
# change data size
sed -i -E "s/^train_data = (.*)/train_data = \1[:100]/" examples/ptb/train_ptb.py
sed -i -E "s/^valid_data = (.*)/valid_data = \1[:100]/" examples/ptb/train_ptb.py
sed -i -E "s/^test_data = (.*)/test_data = \1[:100]/" examples/ptb/train_ptb.py

$run examples/ptb/download.py
$run examples/ptb/train_ptb.py
$run examples/ptb/train_ptb.py --gpu=0

# sentiment
echo "Running sentiment example"

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" examples/sentiment/train_sentiment.py
# change data size
sed -i -E "s/^train_trees = (.*)/train_trees = \1[:10]/" examples/sentiment/train_sentiment.py
sed -i -E "s/^test_trees = (.*)/test_trees = \1[:10]/" examples/sentiment/train_sentiment.py

$run examples/sentiment/download.py
$run examples/sentiment/train_sentiment.py
$run examples/sentiment/train_sentiment.py --gpu=0

# imagenet
echo "Runnig imagenet example"

imagenet_data=../data/imagenet/data.txt
$run examples/imagenet/compute_mean.py -r ../data/imagenet $imagenet_data
$run examples/imagenet/train_imagenet.py -a nin -r ../data/imagenet $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a alexbn -r ../data/imagenet $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a googlenet -r ../data/imagenet $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a googlenetbn -r ../data/imagenet $imagenet_data $imagenet_data

# word2vec
echo "Running word2vec example"

# note that ptb.train.txt is already downloaded

sed -i -E "s/n_vocab = len\(word2index\)/n_vocab = len(word2index)\ndataset = dataset[:100]/" examples/word2vec/train_word2vec.py

$run examples/word2vec/train_word2vec.py -e 1 -b 10
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --gpu=0
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 -m cbow --out-type ns
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 -m cbow --out-type ns --gpu=0
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --out-type original
echo "it" | $run examples/word2vec/search.py
$run examples/word2vec/train_word2vec.py -e 1 -b 10 --out-type original --gpu=0
echo "it" | $run examples/word2vec/search.py

# show coverage
coverage report -m --include="examples/*"
