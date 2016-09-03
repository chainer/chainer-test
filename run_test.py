#!/usr/bin/env python

import argparse
import os

import docker


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'py2', 'py3', 'py35', 'example', 'prev_example', 'doc'
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
            'requires': [
                'setuptools', 'cython', 'numpy<1.12', 'h5py', 'pillow'],
        }
        script = './test.sh'

    elif args.test == 'py3':
        # TODO(unno): Fix this line after protobuf 3 is released
        conf = {
            'base': 'ubuntu14_py3',
            'cuda': 'cuda70',
            'cudnn': 'cudnn4',
            'requires': [
                'setuptools', 'cython', 'numpy<1.11', 'protobuf==3.0.0b3',
                'pillow'],
        }
        script = './test.sh'

    elif args.test == 'py35':
        conf = {
            'base': 'ubuntu14_py35',
            'cuda': 'cuda75',
            'cudnn': 'cudnn51',
            'requires': ['setuptools', 'cython', 'numpy<1.10', 'h5py'],
        }
        script = './test.sh'

    elif args.test == 'example':
        conf = {
            'base': 'centos7_py2',
            'cuda': 'cuda75',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.12'],
        }
        script = './test_example.sh'

    elif args.test == 'prev_example':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda65',
            'cudnn': 'cudnn5',
            'requires': ['setuptools', 'cython', 'numpy<1.11'],
        }
        script = './test_prev_example.sh'

    elif args.test == 'doc':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda70',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.12', 'sphinx']
        }
        script = './test_doc.sh'

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
        if os.path.exists('chainer/coverage.xml'):
            with open('coverage.xml', 'w') as outputs:
                with open('chainer/coverage.xml') as inputs:
                    for line in inputs:
                        outputs.write(
                            line.replace('filename="', 'filename="chainer/'))
