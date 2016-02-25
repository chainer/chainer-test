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
    parser.add_argument('--coveralls')
    parser.add_argument('-i', '--interactive', action='store_true')
    args = parser.parse_args()

    if args.test == 'py2':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda65',
            'cudnn': 'cudnn2',
            'requires': ['setuptools', 'cython', 'numpy<1.11'],
        }
        script = './test.sh'

    elif args.test == 'py3':
        conf = {
            'base': 'ubuntu14_py3',
            'cuda': 'cuda70',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.10'],
        }
        script = './test.sh'

    elif args.test == 'py35':
        conf = {
            'base': 'ubuntu14_py35',
            'cuda': 'cuda75',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.10'],
        }
        script = './test.sh'

    elif args.test == 'example':
        conf = {
            'base': 'centos7_py2',
            'cuda': 'cuda75',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.11'],
        }
        script = './test_example.sh'

    elif args.test == 'prev_example':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda65',
            'cudnn': 'cudnn2',
            'requires': ['setuptools', 'cython', 'numpy<1.10'],
        }
        script = './test_prev_example.sh'

    elif args.test == 'doc':
        conf = {
            'base': 'ubuntu14_py2',
            'cuda': 'cuda70',
            'cudnn': 'cudnn3',
            'requires': ['setuptools', 'cython', 'numpy<1.11', 'sphinx']
        }
        script = './test_doc.sh'

    else:
        raise

    volume = []
    env = {'CUDNN': conf['cudnn']}

    conf['requires'] += ['nose', 'mock', 'coverage']

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
        docker.run_interactive(conf, volume=volume, env=env)
    else:
        docker.run_with(conf, script, volume=volume, env=env)

        # convert coverage.xml
        if os.path.exists('chainer/coverage.xml'):
            with open('coverage.xml', 'w') as outputs:
                with open('chainer/coverage.xml') as inputs:
                    for line in inputs:
                        outputs.write(
                            line.replace('filename="', 'filename="chainer/'))
