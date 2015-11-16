#!/bin/sh -ex

PREV_VER=1.3.2

cd chainer
python setup.py -q develop install
cd ..

if which apt-get; then
  apt-get install -y libjpeg-dev zlib1g-dev
elif which yum; then
  yum -y install libjpeg-devel zlib-devel
else
  echo "both apt-get and yum command are not found"
  exit 1
fi
pip install pillow

curl -L -o v${PREV_VER}.tar.gz https://github.com/pfnet/chainer/archive/v${PREV_VER}.tar.gz
tar xzf v${PREV_VER}.tar.gz
cd chainer-${PREV_VER}/examples

# mnist
echo "Running mnist example"
cd mnist

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" train_mnist.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" train_mnist.py

sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" train_mnist_model_parallel.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" train_mnist_model_parallel.py

python train_mnist.py
python train_mnist.py --gpu=0
python train_mnist_model_parallel.py

cd ..

# ptb
echo "Running ptb example"
cd ptb

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" train_ptb.py
sed -i -E "s/^n_units\s*=\s*[0-9]+/n_units = 10/" train_ptb.py
# change data size
sed -i -E "s/^train_data = (.*)/train_data = \1[:100]/" train_ptb.py
sed -i -E "s/^valid_data = (.*)/valid_data = \1[:100]/" train_ptb.py
sed -i -E "s/^test_data = (.*)/test_data = \1[:100]/" train_ptb.py

python download.py
python train_ptb.py
python train_ptb.py --gpu=0

cd ..

# sentiment
echo "Running sentiment example"
cd sentiment

# change epoch
sed -i -E "s/^n_epoch\s*=\s*[0-9]+/n_epoch = 1/" train_sentiment.py
# change data size
sed -i -E "s/^train_trees = (.*)/train_trees = \1[:10]/" train_sentiment.py
sed -i -E "s/^test_trees = (.*)/test_trees = \1[:10]/" train_sentiment.py

python download.py
python train_sentiment.py
python train_sentiment.py --gpu=0

cd ..

# imagenet
echo "Runnig imagenet example"
cd ../../data/imagenet

python ../../chainer/examples/imagenet/compute_mean.py data.txt
python ../../chainer/examples/imagenet/train_imagenet.py -a nin data.txt data.txt
python ../../chainer/examples/imagenet/train_imagenet.py -a alexbn data.txt data.txt
python ../../chainer/examples/imagenet/train_imagenet.py -a googlenet data.txt data.txt
python ../../chainer/examples/imagenet/train_imagenet.py -a googlenetbn data.txt data.txt

cd ../../chainer/examples

# word2vec
echo "Running word2vec example"

cd word2vec
# note that ptb.train.txt is already downloaded
cp ../ptb/ptb.train.txt .

sed -i -E "s/n_vocab = len\(word2index\)/n_vocab = len(word2index)\ndataset = dataset[:100]/" train_word2vec.py

# search.py is not supported in the latest
python train_word2vec.py -e 1 -b 10
# echo "it" | python search.py
python train_word2vec.py -e 1 -b 10 --gpu=0
# echo "it" | python search.py
python train_word2vec.py -e 1 -b 10 -m cbow --out-type ns
# echo "it" | python search.py
python train_word2vec.py -e 1 -b 10 -m cbow --out-type ns --gpu=0
# echo "it" | python search.py
python train_word2vec.py -e 1 -b 10 --out-type original
# echo "it" | python search.py
python train_word2vec.py -e 1 -b 10 --out-type original --gpu=0
# echo "it" | python search.py

cd ..
