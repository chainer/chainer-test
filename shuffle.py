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
    random.seed(0)
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


def parse_version(version):
    """Parse a version number to make an int list."""
    return [int(num) for num in version.split('.')]


def make_require(name, version):
    version_number = parse_version(version)
    version_number[-1] += 1
    next_ver = '.'.join(str(num) for num in version_number)
    return '%s<%s' % (name, next_ver)


def append_require(params, conf, name):
    version = params.get(name, None)
    if version:
        conf['requires'].append(make_require(name, version))


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

    append_require(params, conf, 'numpy')

    if params.get('h5py', None) == '2.5':
        # NumPy is required to install h5py in this version
        conf['requires'].append('numpy<1.10')
    append_require(params, conf, 'h5py')

    append_require(params, conf, 'theano')

    if params.get('protobuf', None) == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'
    else:
        append_require(params, conf, 'protobuf')

    append_require(params, conf, 'pillow')

    return conf


def make_shuffle_conf(params, index):
    params = get_shuffle_params(params, index)
    for key, value in params.items():
        print('{}: {}'.format(key, value))
    sys.stdout.flush()

    return make_conf(params)
