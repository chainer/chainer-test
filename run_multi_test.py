#!/usr/bin/env python

import argparse

import docker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--base', choices=['ubuntu14_py2', 'ubuntu14_py3', 'ubuntu14_py35', 'centos7_py2', 'centos7_py3'], required=True)
    parser.add_argument('--cuda', choices=['none', 'cuda65', 'cuda70', 'cuda75'], required=True)
    parser.add_argument('--cudnn', choices=['none', 'cudnn2', 'cudnn3', 'cudnn4-rc'], required=True)
    parser.add_argument('--numpy', choices=['numpy19', 'numpy110'], required=True)
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
        ]
    }
    if args.numpy == 'numpy19':
        conf['requires'].append('numpy<1.10')
    elif args.numpy == 'numpy110':
        conf['requires'].append('numpy<1.11')

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    if args.interactive:
        docker.run_interactive(conf, volume=volume, env=env)
    else:
        docker.run_with(conf, './test.sh')
