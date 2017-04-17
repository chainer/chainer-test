#!/usr/bin/env python2

import argparse
import itertools
import os
import random
import sys

import docker
import six

params = {
    'base': docker.base_choices,
    'cuda': docker.cuda_choices,
    'cudnn': docker.cudnn_choices,
    'numpy': ['1.9', '1.10', '1.11', '1.12'],
    'protobuf': ['2', '3', 'cpp-3'],
    'h5py': ['none', '2.5', '2.6', '2.7'],
    'pillow': ['none', '3.4', '4.0', '4.1'],
    'theano': ['none', '0.8', '0.9'],
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

    # avoid SEGV
    if ret['numpy'] == '1.9' and ret['h5py'] != 'none':
        ret['numpy'] = '1.10'

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


    if params['h5py'] == '2.7':
        conf['requires'].append('h5py<2.8')
    elif params['h5py'] == '2.6':
        conf['requires'].append('h5py<2.7')
    elif params['h5py'] == '2.5':
        # h5py uses numpy in its setup script
        conf['requires'].append('numpy<1.10')
        conf['requires'].append('h5py<2.6')

    if params['theano'] == '0.8':
        conf['requires'].append('theano<0.9')
    elif params['theano'] == '0.9':
        conf['requires'].append('theano<1')

    if params['protobuf'] == '3':
        conf['requires'].append('protobuf<4')
    elif params['protobuf'] == '2':
        conf['requires'].append('protobuf<3')
    elif params['protobuf'] == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'

    if params['pillow'] == '3.4':
        conf['requires'].append('pillow<3.5')
    elif params['pillow'] == '4.0':
        conf['requires'].append('pillow<4.1')
    elif params['pillow'] == '4.1':
        conf['requires'].append('pillow<4.2')

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
        if conf['cuda'] != 'none':
            docker.run_with(
                conf, './test.sh', no_cache=args.no_cache, volume=volume, env=env,
                timeout=args.timeout, gpu_id=args.gpu_id)

        docker.run_with(
            conf, './test_cpu.sh', no_cache=args.no_cache, volume=volume, env=env,
            timeout=args.timeout)
