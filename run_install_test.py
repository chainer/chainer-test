#!/usr/bin/env python

import argparse

import docker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for installation')
    parser.add_argument('--base', choices=['ubuntu14_py2', 'ubuntu14_py3', 'ubuntu14_py35', 'centos7_py2', 'centos7_py3'], required=True)
    parser.add_argument('--cuda', choices=['none', 'cuda65', 'cuda70', 'cuda75'], required=True)
    parser.add_argument('--cudnn', choices=['none', 'cudnn2', 'cudnn3', 'cudnn4-rc'], required=True)
    parser.add_argument('--numpy')
    parser.add_argument('--setuptools')
    parser.add_argument('--pip')
    parser.add_argument('--cython')

    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    args = parser.parse_args()

    # make sdist
    build_conf = {
        'base': 'ubuntu14_py2',
        'cuda': 'cuda65',
        'cudnn': 'none',
        'requires': ['cython'],
    }
    docker.run_with(build_conf, './build_sdist.sh')

    conf = {
        'base': args.base,
        'cuda': args.cuda,
        'cudnn': args.cudnn,
        'requires': [],
    }

    if args.numpy:
        conf['requires'].append('numpy=={0}'.format(args.numpy))
    if args.setuptools:
        conf['requires'].append('setuptools=={0}'.format(args.numpy))
    if args.pip:
        conf['requires'].append('pip=={0}'.format(args.numpy))
    if args.cython:
        conf['requires'].append('cython=={0}'.format(args.numpy))

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    docker.run_with(conf, './test_install.sh')
