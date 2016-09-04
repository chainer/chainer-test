#!/bin/sh -ex

pip install -U pip --user

PREV_VER=1.5.1
CHAINER_DIR=chainer-${PREV_VER}

cd chainer
python setup.py -q develop install --user
cd ..

if apt-get --version; then
  apt-get install -y libjpeg-dev zlib1g-dev
elif yum --version; then
  yum -y install libjpeg-devel zlib-devel
else
  echo "both apt-get and yum command are not found"
  exit 1
fi
pip install h5py pillow --user

run=python

curl -L -o v${PREV_VER}.tar.gz https://github.com/pfnet/chainer/archive/v${PREV_VER}.tar.gz
tar xzf v${PREV_VER}.tar.gz
cd ${CHAINER_DIR}

# mnist
echo "Running mnist example"

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" examples/mnist/train_mnist.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" examples/mnist/train_mnist.py

$run examples/mnist/train_mnist.py
$run examples/mnist/train_mnist.py --gpu=0
$run examples/mnist/train_mnist.py --net=parallel

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" examples/ptb/train_ptb.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" examples/ptb/train_ptb.py
sed -i -E "s/bprop_len = 35/bprop_len = 4/" examples/ptb/train_ptb.py
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
sed -i -E "s/^batchsize\s*=\s*[0-9]+/batchsize = 1/" examples/sentiment/train_sentiment.py
sed -i -E "s/^epoch_per_eval\s*=\s*[0-9]+/epoch_per_eval = 1/" examples/sentiment/train_sentiment.py
# change data size
sed -i -E "s/^train_trees = (.*)/train_trees = \1[:10]/" examples/sentiment/train_sentiment.py
sed -i -E "s/^test_trees = (.*)/test_trees = \1[:10]/" examples/sentiment/train_sentiment.py

$run examples/sentiment/download.py
$run examples/sentiment/train_sentiment.py
$run examples/sentiment/train_sentiment.py --gpu=0

# imagenet
echo "Runnig imagenet example"

sed -i -E "s/if count % 100000 == 0/if count % 1 == 0/" examples/imagenet/train_imagenet.py

imagenet_data=../data/imagenet/data.txt
$run examples/imagenet/compute_mean.py -r ../data/imagenet $imagenet_data
$run examples/imagenet/train_imagenet.py -a nin -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a alex -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a alexbn -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a googlenet -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data
$run examples/imagenet/train_imagenet.py -a googlenetbn -r ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data

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
