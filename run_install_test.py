#!/usr/bin/env python2

import argparse
import os

import argconfig
import docker
import shuffle


params = {
    'base': docker.base_choices,
    'cuda': docker.cuda_choices,
    'cudnn': docker.cudnn_choices + ['cudnn-latest-with-dummy'],
    'nccl': docker.nccl_choices,
    'numpy': ['1.9', '1.10', '1.11', '1.12', '1.13'],
    'cython': [None, '0.20', '0.21', '0.23', '0.24'],
    'setuptools': [None, '3.3', '18.2', '18.3.2'],
    'pip': [None, '7', '8', '9'],
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for installation')
    parser.add_argument('--id', type=int, required=True)

    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    build_conf = {
        'base': 'ubuntu14_py2',
        'cuda': 'none',
        'cudnn': 'none',
        'nccl': 'none',
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
    docker.run_with(conf, './test_install.sh', no_cache=args.no_cache,
                    volume=volume, env=env, timeout=args.timeout)
