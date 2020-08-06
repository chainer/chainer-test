#!/bin/sh -ex

. ./environment.sh

pip install -U pip --user

pip install --user -e cupy/

cd chainer
rm -rf dist
python setup.py -q sdist
cd dist
pip install *.tar.gz --user
cd ..

python -m pip install coverage matplotlib nltk progressbar2 --user
python -m pip install olefile --user
python -m pip install --global-option="build_ext" --global-option="--disable-jpeg" pillow --user
#python -m pip install --extra-index-url https://developer.download.nvidia.com/compute/redist nvidia-dali --user
python -m pip install 'https://developer.download.nvidia.com/compute/redist/nvidia-dali/nvidia_dali-0.7.0-624544-cp35-cp35m-manylinux1_x86_64.whl' --user

run="coverage run -a --branch"

export MPLBACKEND=Agg

export OMP_NUM_THREADS=1

# mnist
echo "Running mnist example"

# change epoch
$run examples/mnist/train_mnist.py --epoch=1 --unit=10
$run examples/mnist/train_mnist.py --gpu=0 --epoch=1 --unit=10
if [ -f examples/mnist/train_mnist_custom_loop.py ]; then
  $run examples/mnist/train_mnist_custom_loop.py --epoch=1 --unit=10
  $run examples/mnist/train_mnist_custom_loop.py --gpu=0 --epoch=1 --unit=10
fi
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

$run examples/imagenet/train_imagenet.py --dali --gpu=0 --test -a nin -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data

$run examples/imagenet/train_imagenet.py --dali --gpu=0 --dtype=float16 --test -a nin -R ../data/imagenet -B 1 -b 1 -E 1 $imagenet_data $imagenet_data

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

# seq2seq
$run examples/seq2seq/seq2seq.py ../data/seq2seq/source.txt ../data/seq2seq/target.txt ../data/seq2seq/source.vocab.txt ../data/seq2seq/target.vocab.txt --unit 8  --validation-source ../data/seq2seq/source.txt --validation-target ../data/seq2seq/target.txt --validation-interval 1
$run examples/seq2seq/seq2seq.py ../data/seq2seq/source.txt ../data/seq2seq/target.txt ../data/seq2seq/source.vocab.txt ../data/seq2seq/target.vocab.txt --unit 8  --validation-source ../data/seq2seq/source.txt --validation-target ../data/seq2seq/target.txt --validation-interval 1 --gpu=0

# text classification
echo "Text classification example"

$run examples/text_classification/train_text_classifier.py --dataset dbpedia -e 1 -b 1 --test
$run examples/text_classification/train_text_classifier.py --dataset dbpedia --gpu=0 -e 1 -b 1 --test

# show coverage
coverage report -m --include="examples/*"
coverage xml --include="examples/*"
