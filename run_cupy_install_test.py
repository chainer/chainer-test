#!/usr/bin/env python

import argparse
import os

import argconfig
import docker
import shuffle
import version


params = {
    'base': None,
    'cuda_cudnn_nccl': docker.get_cuda_cudnn_nccl_choices('cupy', with_dummy=True),
    'numpy': ['1.9', '1.10', '1.11', '1.12'],
    'cython': [None, '0.28.0', '0.29.13'],
    'pip': [None, '7', '8', '9', '10'],
    'wheel': [False, True],
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for installation')
    parser.add_argument('--id', type=int, required=True)

    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='2h')
    parser.add_argument('-i', '--interactive', action='store_true')

    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if version.is_master_branch('cupy'):
        params['base'] = docker.base_choices_master
    else:
        params['base'] = docker.base_choices_stable_cupy

    # make sdist
    # cuda, cudnn and numpy is required to make a sdist file.
    build_conf = {
        'base': 'ubuntu16_py27',
        'cuda': 'cuda80',
        'cudnn': 'cudnn5-cuda8',
        'nccl': 'none',
        'requires': ['cython==0.29.13', 'numpy==1.9.3'],
    }
    volume = []
    env = {}
    argconfig.parse_args(args, env, build_conf, volume)
    docker.run_with(build_conf, './build_sdist_cupy.sh', volume=volume,
                    env=env)

    conf = shuffle.make_shuffle_conf(params, args.id)
    volume = []
    env = {}
    argconfig.parse_args(args, env, conf, volume)
    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env,
            use_root=args.root)
    else:
        docker.run_with(
            conf, './test_cupy_install.sh', no_cache=args.no_cache,
            volume=volume, env=env, timeout=args.timeout, use_root=args.root)
