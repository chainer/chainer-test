#!/usr/bin/env python

import argparse

import docker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--base', choices=docker.base_choices, required=True)
    parser.add_argument('--cuda', choices=docker.cuda_choices, required=True)
    parser.add_argument('--cudnn', choices=docker.cudnn_choices, required=True)
    parser.add_argument('--numpy', choices=['1.9', '1.10'], required=True)
    parser.add_argument('--h5py', choices=['none', '2.5'])
    parser.add_argument('--type', choices=['cpu', 'gpu'], required=True)
    parser.add_argument('--cupy-cache')
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()

    conf = {
        'base': args.base,
        'cuda': args.cuda,
        'cudnn': args.cudnn,
        'requires': [
            'cython',
            'nose',
            'mock',
            'coverage',
        ]
    }
    volume = []
    env = {}

    if args.numpy == '1.9':
        conf['requires'].append('numpy<1.10')
    elif args.numpy == '1.10':
        conf['requires'].append('numpy<1.11')

    if args.h5py == '2.5':
        conf['requires'].append('h5py<2.6')

    if args.cupy_cache:
        volume.append(args.cupy_cache)
        env['CUPY_CACHE_DIR'] = args.cupy_cache

    if args.type == 'cpu':
        script = './test_cpu.sh'
    elif args.type == 'gpu':
        script = './test.sh'

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    if args.interactive:
        docker.run_interactive(conf, volume=volume, env=env)
    else:
        docker.run_with(conf, script, volume=volume, env=env)
