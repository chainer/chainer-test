#!/usr/bin/env python2

import argparse
import os

import argconfig
import docker
import version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'chainer-py2', 'chainer-py3', 'chainer-py35', 'chainer-slow',
        'chainer-example', 'chainer-prev_example', 'chainer-doc',
        'cupy-py2', 'cupy-py3', 'cupy-py35', 'cupy-slow',
        'cupy-example', 'cupy-doc',
    ], required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument(
        '--clone-cupy', action='store_true',
        help='clone cupy repository based on chainer version. '
        'this option is used for testing chainer.')
    parser.add_argument(
        '--clone-chainer', action='store_true',
        help='clone chainer repository based on cupy version. '
        'this option is used for testing cupy.')
    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if args.clone_cupy:
        version.clone_cupy()
    if args.clone_chainer:
        version.clone_chainer()

    if args.test == 'chainer-py2':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.26.1', 'numpy<1.14',
                'scipy<0.19', 'h5py', 'theano', 'pillow',
                'protobuf',  # ignore broken protobuf 3.2.0rc1
            ]
        }
        script = './test.sh'

    elif args.test == 'chainer-py3':
        conf = {
            'base': 'ubuntu14_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn51-cuda8',
            'nccl': 'nccl1.3.4',
            'protobuf-cpp': 'protobuf-cpp-3',
            'requires': [
                'setuptools', 'pip', 'cython==0.26.1', 'numpy<1.12',
                'pillow',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-py35':
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda90',
            'cudnn': 'cudnn7-cuda9',
            'nccl': 'nccl2.0-cuda9',
            'requires': [
                'setuptools', 'cython==0.26.1', 'numpy<1.10',
                'scipy<0.19', 'h5py', 'theano', 'protobuf<3',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-slow':
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3.4',
            'requires': [
                'setuptools', 'cython==0.26.1', 'numpy<1.11',
                'scipy<0.19', 'h5py', 'theano', 'protobuf<3',
            ],
        }
        script = './test_slow.sh'

    elif args.test == 'chainer-example':
        conf = {
            'base': 'centos7_py2',
            'cuda': 'cuda75',
            'cudnn': 'cudnn6',
            'nccl': 'nccl1.3.4',
            'requires': ['setuptools', 'cython==0.26.1', 'numpy<1.13'],
        }
        script = './test_example.sh'

    elif args.test == 'chainer-prev_example':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda90',
            'cudnn': 'cudnn7-cuda9',
            'nccl': 'none',
            'requires': ['setuptools', 'pip', 'cython==0.26.1', 'numpy<1.12'],
        }
        script = './test_prev_example.sh'

    elif args.test == 'chainer-doc':
        # See sphinx version RTD uses:
        # https://github.com/rtfd/readthedocs.org/blob/master/requirements/pip.txt
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.26.1', 'numpy<1.13',
                'scipy<0.19', 'theano', 'sphinx==1.5.3', 'sphinx_rtd_theme',
            ]
        }
        script = './test_doc.sh'

    elif args.test == 'cupy-py2':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.26.1', 'numpy<1.14',
                'scipy<0.19',
            ]
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3':
        conf = {
            'base': 'ubuntu14_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3.4',
            'protobuf-cpp': 'protobuf-cpp-3',
            'requires': [
                'setuptools', 'pip', 'cython==0.26.1', 'numpy<1.12',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py35':
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda90',
            'cudnn': 'cudnn7-cuda9',
            'nccl': 'nccl2.0-cuda9',
            'requires': [
                'setuptools', 'cython==0.26.1', 'numpy<1.10', 'scipy<0.19',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-slow':
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'setuptools', 'cython==0.26.1', 'numpy<1.11', 'scipy<0.19',
            ],
        }
        script = './test_cupy_slow.sh'

    elif args.test == 'cupy-example':
        conf = {
            'base': 'centos7_py2',
            'cuda': 'cuda75',
            'cudnn': 'cudnn5',
            'nccl': 'nccl1.3.4',
            'requires': [
                'setuptools', 'cython==0.26.1', 'numpy<1.13', 'scipy<0.19',
            ],
        }
        script = './test_cupy_example.sh'

    elif args.test == 'cupy-doc':
        # See sphinx version RTD uses:
        # https://github.com/rtfd/readthedocs.org/blob/master/requirements/pip.txt
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3.4',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.26.1', 'numpy<1.13',
                'scipy<0.19', 'sphinx==1.5.3', 'sphinx_rtd_theme',
            ]
        }
        script = './test_cupy_doc.sh'

    else:
        raise

    volume = []
    env = {'CUDNN': conf['cudnn']}
    conf['requires'] += [
        'pytest',
        'pytest-timeout',  # For timeout
        'pytest-cov',  # For coverage report
        'nose',
        'mock',
        'coveralls']

    argconfig.parse_args(args, env, conf, volume)

    # coverage result is reported when the same type of a test is executed
    if args.coveralls_repo and args.coveralls_repo in args.test:
        argconfig.set_coveralls(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        docker.run_with(
            conf, script, no_cache=args.no_cache, volume=volume, env=env,
            timeout=args.timeout, gpu_id=args.gpu_id)
