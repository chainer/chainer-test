#!/usr/bin/env python2

import argparse
import os

import docker


def append_requires(requires, name, ver):
    if ver and ver != 'none':
        requires.append('%s==%s' % (name, ver))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for installation')
    parser.add_argument('--base', choices=docker.base_choices, required=True)
    parser.add_argument('--cuda', choices=docker.cuda_choices, required=True)
    parser.add_argument('--cudnn', choices=docker.cudnn_choices +
                        ['cudnn-latest-with-dummy'], required=True)
    parser.add_argument('--numpy')
    parser.add_argument('--setuptools')
    parser.add_argument('--pip')
    parser.add_argument('--cython')

    parser.add_argument('--cache')
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    args = parser.parse_args()

    # make sdist
    # cuda, cudnn and numpy is required to make a sdist file.
    build_conf = {
        'base': 'ubuntu14_py2',
        'cuda': 'cuda65',
        'cudnn': 'cudnn2',
        'requires': ['cython==0.24', 'numpy==1.9.3'],
    }
    volume = []
    env = {}

    if args.cache:
        volume.append(args.cache)
        env['CUPY_CACHE_DIR'] = os.path.join(args.cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(args.cache, '.ccache')

    docker.run_with(build_conf, './build_sdist.sh', volume=volume, env=env)

    conf = {
        'base': args.base,
        'cuda': args.cuda,
        'cudnn': args.cudnn,
        'requires': [],
    }

    append_requires(conf['requires'], 'setuptools', args.setuptools)
    append_requires(conf['requires'], 'pip', args.pip)
    append_requires(conf['requires'], 'cython', args.cython)
    append_requires(conf['requires'], 'numpy', args.numpy)

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    docker.run_with(conf, './test_install.sh', no_cache=args.no_cache,
                    volume=volume, env=env, timeout=args.timeout)
