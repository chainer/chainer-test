#!/usr/bin/env python2

import argparse
import itertools
import os
import random
import sys

import docker
import six


cuda_choices = list(docker.cuda_choices)
cuda_choices.remove('none')
cuda_choices.remove('cuda65')

params = {
    'base': docker.base_choices,
    'cuda': cuda_choices,
    'cudnn': docker.cudnn_choices,
    'nccl': docker.nccl_choices,
    'numpy': ['1.9', '1.10', '1.11', '1.12'],
}


def iter_shuffle(lst):
    while True:
        l = list(lst)
        random.shuffle(l)
        for x in l:
            yield x


def get_shuffle_params(params, index):
    keys = params.keys()
    iters = [iter_shuffle(params[key]) for key in keys]
    vals = next(itertools.islice(six.moves.zip(*iters), index, None))
    ret = dict(zip(keys, vals))

    # Avoid this combination because NCCL is not supported or cannot built
    if 'centos6' in ret['base'] or ret['cuda'] in ('none', 'cuda65'):
        ret['nccl'] = 'none'

    return ret


if __name__ == '__main__':
    random.seed(0)

    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--cache')
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    parser.add_argument(
        '--gpu-id', type=int,
        help='GPU ID you want to use mainly in the script.')
    parser.add_argument('--interactive', action='store_true')
    args = parser.parse_args()

    params = get_shuffle_params(params, args.id)
    for key, value in params.items():
        print('{}: {}'.format(key, value))
    sys.stdout.flush()

    conf = {
        'base': params['base'],
        'cuda': params['cuda'],
        'cudnn': params['cudnn'],
        'nccl': params['nccl'],
        'requires': ['setuptools', 'pip', 'cython==0.24'],
    }

    volume = []
    env = {'CUDNN': conf['cudnn']}

    if params['numpy'] == '1.9':
        conf['requires'].append('numpy<1.10')
    elif params['numpy'] == '1.10':
        conf['requires'].append('numpy<1.11')
    elif params['numpy'] == '1.11':
        conf['requires'].append('numpy<1.12')
    elif params['numpy'] == '1.12':
        conf['requires'].append('numpy<1.13')

    conf['requires'] += [
        'hacking',
        'nose',
        'mock',
        'coverage',
    ]

    if args.cache:
        volume.append(args.cache)
        env['CUPY_CACHE_DIR'] = os.path.join(args.cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(args.cache, '.ccache')

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        docker.run_with(
            conf, './test_cupy.sh', no_cache=args.no_cache, volume=volume,
            env=env, timeout=args.timeout, gpu_id=args.gpu_id)
