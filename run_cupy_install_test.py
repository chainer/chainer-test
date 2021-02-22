#!/usr/bin/env python

import argparse
import os

import argconfig
import docker
import shuffle
import version


params = {
    'base': None,
    'cuda_libs': docker.get_cuda_libs_choices('cupy', with_dummy=True),
    'numpy': ['1.17', '1.18', '1.19'],
    'cython': ['0.29.22'],
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
        params['base'] = docker.base_choices_master_cupy
    else:
        params['base'] = docker.base_choices_stable_cupy

    # make sdist
    # cuda, cudnn and numpy is required to make a sdist file.
    build_conf = {
        'base': 'ubuntu18_py36',
        'cuda': 'cuda100',
        'cudnn': 'cudnn76-cuda100',
        'nccl': 'none',
        'cutensor': 'none',
        'requires': ['cython==0.29.22', 'numpy==1.17.5'],
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
