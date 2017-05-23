#!/usr/bin/env python2

import argparse
import os

import docker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'py2', 'py3', 'py35', 'doc'
    ], required=True)
    parser.add_argument('--cache')
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='1h')
    parser.add_argument('--coveralls')
    parser.add_argument(
        '--gpu-id', type=int,
        help='GPU ID you want to use mainly in the script.')
    parser.add_argument('-i', '--interactive', action='store_true')
    args = parser.parse_args()

    if args.test == 'py2':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda65',
            'cudnn': 'cudnn2',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.24', 'numpy<1.13',
            ]
        }
        script = './test_cupy.sh'

    elif args.test == 'py3':
        conf = {
            'base': 'ubuntu14_py3',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'nccl': 'nccl1.3.4',
            'protobuf-cpp': 'protobuf-cpp-3',
            'requires': [
                'setuptools', 'pip', 'cython==0.24', 'numpy<1.12',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'py35':
        conf = {
            'base': 'ubuntu16_py3',
            'cuda': 'cuda80',
            'cudnn': 'cudnn51',
            'nccl': 'none',
            'requires': ['setuptools', 'cython==0.24', 'numpy<1.11'],
        }
        script = './test_cupy.sh'

    elif args.test == 'doc':
        # See sphinx version RTD uses:
        # https://github.com/rtfd/readthedocs.org/blob/master/requirements/pip.txt
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda70',
            'cudnn': 'cudnn3',
            'nccl': 'nccl1.3.4',
            'requires': ['setuptools', 'cython==0.24', 'numpy<1.13',
                         'sphinx==1.5.3']
        }
        script = './test_cupy_doc.sh'

    else:
        raise

    volume = []
    env = {'CUDNN': conf['cudnn']}

    conf['requires'] += ['hacking', 'nose', 'mock', 'coverage']

    if args.cache:
        volume.append(args.cache)
        env['CUPY_CACHE_DIR'] = os.path.join(args.cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(args.cache, '.ccache')

    if args.coveralls and args.test == 'py2':
        env['COVERALLS_REPO_TOKEN'] = args.coveralls
        conf['requires'].append('coveralls')

    if args.http_proxy:
        conf['http_proxy'] = args.http_proxy
    if args.https_proxy:
        conf['https_proxy'] = args.https_proxy

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        docker.run_with(
            conf, script, no_cache=args.no_cache, volume=volume, env=env,
            timeout=args.timeout, gpu_id=args.gpu_id)

        # convert coverage.xml
        if os.path.exists('cupy/coverage.xml'):
            with open('coverage.xml', 'w') as outputs:
                with open('cupy/coverage.xml') as inputs:
                    for line in inputs:
                        outputs.write(
                            line.replace('filename="', 'filename="cupy/'))
