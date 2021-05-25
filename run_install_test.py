#!/usr/bin/env python

import argparse
import os

import argconfig
import docker
import shuffle
import version


params = {
    'base': None,
    'cuda_libs': docker.get_cuda_libs_choices('chainer', with_dummy=True),
    'numpy': ['1.9', '1.10', '1.11', '1.12'],
    # Chainer does not require Cython, so it should be able to be installed
    # with any Cython version.
    'cython': [None, '0.28.0', '0.29.13'],
    'pip': [None, '7', '8', '9'],
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

    if version.is_master_branch('chainer'):
        params['base'] = docker.base_choices_master_chainer
    else:
        params['base'] = docker.base_choices_stable_chainer

    build_conf = {
        'base': 'ubuntu16_py35',
        'cuda': 'none',
        'cudnn': 'none',
        'nccl': 'none',
        'cutensor': 'none',
        'cusparselt': 'none',
        'requires': [],
    }
    volume = []
    env = {}
    argconfig.parse_args(args, env, build_conf, volume)
    docker.run_with(build_conf, './build_sdist.sh', volume=volume, env=env)

    conf = shuffle.make_shuffle_conf(params, args.id)
    volume = []
    env = {}
    argconfig.parse_args(args, env, conf, volume)
    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        docker.run_with(conf, './test_install.sh', no_cache=args.no_cache,
                        volume=volume, env=env, timeout=args.timeout)
