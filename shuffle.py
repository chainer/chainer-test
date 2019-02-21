import itertools
import random
import sys

import six

import docker


def iter_shuffle(lst):
    while True:
        ls = list(lst)
        random.shuffle(ls)
        for x in ls:
            yield x


def _is_ideep_supported(python_version):
    # https://github.com/intel/ideep#requirements
    pyver = python_version
    if pyver[0] == 2:
        return pyver >= (2, 7, 6)
    assert pyver[0] == 3
    if pyver[:2] == (3, 5):
        return pyver >= (3, 5, 2)
    if pyver[:2] == (3, 6):
        return True
    if pyver[:2] == (3, 7):
        return True
    return False


def get_shuffle_params(params, index):
    random.seed(0)
    keys = sorted(params.keys())
    iters = [iter_shuffle(params[key]) for key in keys]
    vals = next(itertools.islice(six.moves.zip(*iters), index, None))
    ret = dict(zip(keys, vals))

    # avoid SEGV
    if ret['numpy'] == '1.9' and ret.get('h5py'):
        ret['numpy'] = '1.10'

    py_ver = docker.get_python_version(ret['base'])

    # Avoid unsupported NumPy/SciPy version for the Python version.
    if py_ver[:2] == (3, 5):
        # Python 3.5 is first supported in NumPy 1.11.
        if ret['numpy'] in ['1.9', '1.10']:
            ret['numpy'] = '1.11'
    elif py_ver[:2] == (3, 6):
        # Python 3.6 is first supported in NumPy 1.12.
        if ret['numpy'] in ['1.9', '1.10', '1.11']:
            ret['numpy'] = '1.12'
        # Python 3.6 is first supported in SciPy 0.19.
        if ret.get('scipy', None) in ['0.18']:
            ret['scipy'] = '0.19'
    elif py_ver[:2] == (3, 7):
        # Python 3.7 is first supported in NumPy 1.14.4.
        if ret['numpy'] in ['1.9', '1.10', '1.11', '1.12', '1.13']:
            ret['numpy'] = '1.14'
        # Python 3.7 is first supported in SciPy 1.0.
        if ret.get('scipy', None) in ['0.18', '0.19']:
            ret['scipy'] = '1.0'

    # iDeep requirements:
    # - Ubuntu 16.04 or CentOS 7.4 or OS X
    # - NumPy 1.13.0+ with Python 2.7/3.5/3.6
    # - NumPy 1.16.0+ with Python 3.7+
    if ret.get('ideep'):
        base = ret['base']
        if (('centos6' in base or 'ubuntu14' in base) or
                not _is_ideep_supported(py_ver)):
            ret['ideep'] = None
        elif py_ver[:2] >= (3, 7):
            if ret['numpy'] in ['1.9', '1.10', '1.11', '1.12', '1.13', '1.14', '1.15']:
                ret['numpy'] = '1.16'
        else:
            if ret['numpy'] in ['1.9', '1.10', '1.11', '1.12']:
                ret['numpy'] = '1.13'

    # Theano 1.0.3 or earlier does not support NumPy 1.16
    if ret.get('theano') in ['0.8', '0.9']:
        if ret['numpy'] == '1.16':
            ret['theano'] = '1.0'

    cuda, cudnn, nccl = ret['cuda_cudnn_nccl']
    if ('centos6' in ret['base'] or
            'ubuntu16' in ret['base'] and cuda < 'cuda8'):
        # nccl is not supported on these environment
        ret['cuda_cudnn_nccl'] = (cuda, cudnn, 'none')

    if 'centos6' in ret['base'] and ret.get('protobuf') == 'cpp-3':
        ret['protobuf'] = '3'

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
    version = params.get(name)
    if version:
        overwrite_requires_version(conf, name, make_require(name, version))


def overwrite_requires_version(conf, name, requirement):
    # Overwrite the requirements for the package `name` already
    # defined in `requires`.
    _, conf['requires'] = docker.partition_requirements(name, conf['requires'])
    conf['requires'].append(requirement)


def make_conf(params):
    conf = {
        'requires': [],
    }

    if 'base' in params:
        conf['base'] = params['base']
    if 'cuda_cudnn_nccl' in params:
        conf['cuda'], conf['cudnn'], conf['nccl'] = params['cuda_cudnn_nccl']

    append_require(params, conf, 'setuptools')
    append_require(params, conf, 'pip')
    append_require(params, conf, 'cython')
    append_require(params, conf, 'numpy')
    append_require(params, conf, 'scipy')

    # Note: h5py 2.5 uses NumPy in its setup script, so NumPy needs to be
    # installed before h5py.
    append_require(params, conf, 'h5py')

    append_require(params, conf, 'theano')

    if params.get('protobuf') == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'
    else:
        append_require(params, conf, 'protobuf')

    ideep = params.get('ideep')
    if ideep is not None:
        overwrite_requires_version(
            conf, 'ideep4py', make_require('ideep4py', ideep))

    append_require(params, conf, 'pillow')

    if params.get('wheel') is True:
        conf['requires'].append('wheel')

    return conf


def make_shuffle_conf(params, index):
    params = get_shuffle_params(params, index)

    print('--- Shuffle Parameters ---')
    for key, value in params.items():
        print('{}: {}'.format(key, value))
    sys.stdout.flush()

    conf = make_conf(params)

    print('--- Configuration ---')
    for key, value in conf.items():
        print('{}: {}'.format(key, value))
    sys.stdout.flush()

    return conf
