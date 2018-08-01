#!/usr/bin/env python2

import argparse
import os

import argconfig
import docker
import version


# Simulate the build environment of ReadTheDocs.
# https://github.com/rtfd/readthedocs.org/blob/master/readthedocs/doc_builder/python_environments.py
# Some packages are omitted as we have our own requirements.
SPHINX_REQUIREMENTS = [
    'Pygments==2.2.0',
    'docutils==0.13.1',
    # 'mock==1.0.1',
    # 'pillow==2.6.1',
    'alabaster>=0.7,<0.8,!=0.7.5',
    'commonmark==0.5.4',
    'recommonmark==0.4.0',
    'sphinx<1.8',
    'sphinx-rtd-theme<0.5',
]


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
    parser.add_argument('--timeout', default='2h')
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
            'base': 'ubuntu14_py27',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.28.0', 'numpy<1.10',
                'scipy<0.19', 'h5py', 'theano', 'pillow',
                'protobuf',  # ignore broken protobuf 3.2.0rc1
            ]
        }
        script = './test.sh'

    elif args.test == 'chainer-py3':
        conf = {
            'base': 'ubuntu14_py34',
            'cuda': 'cuda80',
            'cudnn': 'cudnn51-cuda8',
            'nccl': 'nccl1.3',
            'protobuf-cpp': 'protobuf-cpp-3',
            'requires': [
                'setuptools', 'pip', 'cython==0.28.3', 'numpy<1.12',
                'pillow',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-py35':
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda92',
            'cudnn': 'cudnn71-cuda92',
            'nccl': 'nccl2.2-cuda92',
            'requires': [
                'setuptools', 'cython==0.28.3', 'numpy<1.15',
                'scipy<0.19', 'h5py', 'theano', 'protobuf<3',
                'ideep4py<1.1',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-slow':
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'setuptools', 'cython==0.28.3', 'numpy<1.15',
                'scipy<0.19', 'h5py', 'theano', 'protobuf<3',
                'pillow',
                'ideep4py<1.1',
            ],
        }
        script = './test_slow.sh'

    elif args.test == 'chainer-example':
        conf = {
            'base': 'centos7_py27',
            'cuda': 'cuda75',
            'cudnn': 'cudnn6',
            'nccl': 'nccl1.3',
            'requires': ['setuptools', 'cython==0.28.3', 'numpy<1.13'],
        }
        script = './test_example.sh'

    elif args.test == 'chainer-prev_example':
        conf = {
            'base': 'ubuntu14_py27',
            'cuda': 'cuda90',
            'cudnn': 'cudnn7-cuda9',
            'nccl': 'none',
            'requires': ['setuptools', 'pip', 'cython==0.28.3', 'numpy<1.12'],
        }
        script = './test_prev_example.sh'

    elif args.test == 'chainer-doc':
        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.28.3', 'matplotlib',
                'numpy>=1.14', 'scipy<0.19', 'theano',
            ] + SPHINX_REQUIREMENTS
        }
        script = './test_doc.sh'

    elif args.test == 'cupy-py2':
        conf = {
            'base': 'ubuntu14_py27',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.28.3', 'numpy<1.15',
                'scipy<0.19',
            ]
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3':
        conf = {
            'base': 'ubuntu14_py34',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'protobuf-cpp': 'protobuf-cpp-3',
            'requires': [
                'setuptools', 'pip', 'cython==0.28.0', 'numpy<1.12',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py35':
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda91',
            'cudnn': 'cudnn7-cuda91',
            'nccl': 'nccl2.1-cuda91',
            'requires': [
                'setuptools', 'cython==0.28.3', 'numpy<1.10', 'scipy<0.19',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-slow':
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'setuptools', 'cython==0.28.3', 'numpy<1.11', 'scipy<0.19',
            ],
        }
        script = './test_cupy_slow.sh'

    elif args.test == 'cupy-example':
        conf = {
            'base': 'centos7_py27',
            'cuda': 'cuda75',
            'cudnn': 'cudnn5',
            'nccl': 'nccl1.3',
            'requires': [
                'setuptools', 'cython==0.28.3', 'numpy<1.13', 'scipy<0.19',
            ],
        }
        script = './test_cupy_example.sh'

    elif args.test == 'cupy-doc':
        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.28.3', 'numpy>=1.14',
                'scipy<0.19',
            ] + SPHINX_REQUIREMENTS
        }
        script = './test_cupy_doc.sh'

    else:
        raise

    use_ideep = any(['ideep4py' in req for req in conf['requires']])

    volume = []
    env = {
        'CUDNN': conf['cudnn'],
        'IDEEP': 'ideep4py' if use_ideep else 'none',
    }
    conf['requires'] += [
        'pytest',
        'pytest-timeout',  # For timeout
        'pytest-cov',  # For coverage report
        'nose',
        'mock',
        'coveralls',
        'codecov',
    ]

    argconfig.parse_args(args, env, conf, volume)

    # coverage result is reported when the same type of a test is executed
    if args.coverage_repo and args.coverage_repo in args.test:
        argconfig.setup_coverage(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env,
            use_root=args.root)
    else:
        docker.run_with(
            conf, script, no_cache=args.no_cache, volume=volume, env=env,
            timeout=args.timeout, gpu_id=args.gpu_id, use_root=args.root)
