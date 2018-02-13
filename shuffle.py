import itertools
import random
import sys

import six

import docker


def iter_shuffle(lst):
    while True:
        l = list(lst)
        random.shuffle(l)
        for x in l:
            yield x


def _is_ideep_supported(python_version):
    pyver = python_version
    if pyver[0] == 2:
        return pyver >= (2, 7, 5)
    assert pyver[0] == 3
    if pyver[:2] < (3, 5):
        return False
    if pyver[:2] == (3, 5):
        return pyver >= (3, 5, 2)
    return True


def get_shuffle_params(params, index):
    random.seed(0)
    keys = params.keys()
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
        # Python 3.6 is first supported in SciPy 1.19.
        if ret.get('scipy', None) in ['0.18']:
            ret['scipy'] = '0.19'

    # Avoid iDeep in unsupported Python versions
    if not _is_ideep_supported(py_ver):
        ret['ideep'] = None

    # TODO(kmaehashi) Currently iDeep can only be tested on Ubuntu.
    if not 'ubuntu' in ret['base']:
        ret['ideep'] = None

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

    if params.get('h5py') == '2.5':
        # NumPy is required to install h5py in this version
        overwrite_requires_version(conf, 'numpy', 'numpy<1.10')
    append_require(params, conf, 'h5py')

    append_require(params, conf, 'theano')

    if params.get('protobuf') == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'
    else:
        append_require(params, conf, 'protobuf')

    if params.get('ideep') is not None:
        append_require(
            params, conf, 'ideep4py=={}'.format(params.get('ideep')))

    append_require(params, conf, 'pillow')

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
