import itertools
import random
import sys

import six


def iter_shuffle(lst):
    while True:
        l = list(lst)
        random.shuffle(l)
        for x in l:
            yield x


def get_shuffle_params(params, index):
    keys = params.keys()
    iters = [iter_shuffle(params[key]) for key in keys]
    vals = next(itertools.islice(six.moves.zip(*iters), index, None))
    ret = dict(zip(keys, vals))

    # avoid SEGV
    if ret['numpy'] == '1.9' and ret.get('h5py', 'none') != 'none':
        ret['numpy'] = '1.10'

    # nccl is only supported on CUDA8
    if 'centos6' in ret['base'] or \
       ret['cuda'] == 'none' or \
       ('ubuntu16' in ret['base'] and ret['cuda'] != 'cuda80'):
        ret['nccl'] = 'none'

    return ret


def make_conf(params):
    conf = {
        'requires': [],
    }

    if 'base' in params:
        conf['base'] = params['base']
    if 'cuda' in params:
        conf['cuda'] = params['cuda']
    if 'cudnn' in params:
        conf['cudnn'] = params['cudnn']
    if 'nccl' in params:
        conf['nccl'] = params['nccl']

    numpy = params.get('numpy', None)
    if numpy == '1.9':
        conf['requires'].append('numpy<1.10')
    elif numpy == '1.10':
        conf['requires'].append('numpy<1.11')
    elif numpy == '1.11':
        conf['requires'].append('numpy<1.12')
    elif numpy == '1.12':
        conf['requires'].append('numpy<1.13')

    h5py = params.get('h5py', None)
    if h5py == '2.7':
        conf['requires'].append('h5py<2.8')
    elif h5py == '2.6':
        conf['requires'].append('h5py<2.7')
    elif h5py == '2.5':
        # h5py uses numpy in its setup script
        conf['requires'].append('numpy<1.10')
        conf['requires'].append('h5py<2.6')

    theano = params.get('theano', None)
    if theano == '0.8':
        conf['requires'].append('theano<0.9')
    elif theano == '0.9':
        conf['requires'].append('theano<0.10')

    protobuf = params.get('protobuf', None)
    if protobuf == '3':
        conf['requires'].append('protobuf<4')
    elif protobuf == '2':
        conf['requires'].append('protobuf<3')
    elif protobuf == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'

    pillow = params.get('pillow', None)
    if pillow == '3.4':
        conf['requires'].append('pillow<3.5')
    elif pillow == '4.0':
        conf['requires'].append('pillow<4.1')
    elif pillow == '4.1':
        conf['requires'].append('pillow<4.2')

    return conf



def make_shuffle_conf(params, index):
    params = get_shuffle_params(params, index)
    for key, value in params.items():
        print('{}: {}'.format(key, value))
    sys.stdout.flush()

    return make_conf(params)
