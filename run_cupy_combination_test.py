#!/usr/bin/env python

import argparse
import os
import random

import argconfig
import docker
import shuffle
import version


params = {
    'base': None,
    'cuda_cudnn_nccl': docker.get_cuda_cudnn_nccl_choices('cupy'),
    'numpy': docker.get_numpy_choices(),
    'scipy': [None, '0.19', '1.0'],
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='2h')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument(
        '--clone-chainer', action='store_true',
        help='clone chainer repository based on cupy version.')

    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if version.is_master_branch('cupy'):
        params['base'] = docker.base_choices_master
    else:
        params['base'] = docker.base_choices_stable_cupy

    if args.clone_chainer:
        version.clone_chainer()

    conf = shuffle.make_shuffle_conf(params, args.id)

    # pip has dropped Python 3.4 support since 19.2.
    # TODO(niboshi): More generic and elegant approach to handle special requirements.
    pip_require = 'pip<19.2' if docker.get_python_version(conf['base'])[:2] == (3, 4) else 'pip'

    conf['requires'] = [
        'setuptools',
        pip_require,
        'cython==0.29.13'
    ] + conf['requires'] + [
        'attrs<19.2.0',
        'pytest<4.2',
        'pytest-timeout',  # For timeout
        'pytest-cov',  # For coverage report
        'nose',
        'mock',
        'coverage',
        'coveralls',
        'codecov',
    ]

    volume = []
    env = {'CUDNN': conf['cudnn']}

    argconfig.parse_args(args, env, conf, volume)
    argconfig.setup_coverage(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env,
            use_root=args.root)
    else:
        docker.run_with(
            conf, './test_cupy.sh', no_cache=args.no_cache, volume=volume,
            env=env, timeout=args.timeout, gpu_id=args.gpu_id,
            use_root=args.root)
