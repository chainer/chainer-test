#!/usr/bin/env python2

import argparse
import os
import random

import argconfig
import docker
import shuffle
import version


params = {
    'base': docker.base_choices,
    'cuda_cudnn': docker.get_cuda_cudnn_choices('cupy'),
    'nccl': docker.nccl_choices,
    'numpy': docker.get_numpy_choices(),
    'scipy': [None, '0.18'],
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument(
        '--clone-chainer', action='store_true',
        help='clone chainer repository based on cupy version.')

    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if args.clone_chainer:
        version.clone_chainer()

    conf = shuffle.make_shuffle_conf(params, args.id)
    conf['requires'] = [
        'setuptools',
        'pip',
        'cython==0.26.1'
    ] + conf['requires'] + [
        'nose',
        'mock',
        'coverage',
        'coveralls',
    ]

    volume = []
    env = {'CUDNN': conf['cudnn']}

    argconfig.parse_args(args, env, conf, volume)
    argconfig.set_coveralls(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        docker.run_with(
            conf, './test_cupy.sh', no_cache=args.no_cache, volume=volume,
            env=env, timeout=args.timeout, gpu_id=args.gpu_id)
