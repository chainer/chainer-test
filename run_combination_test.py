#!/usr/bin/env python2

import argparse

import argconfig
import docker
import shuffle
import version


params = {
    'base': docker.base_choices,
    'cuda_cudnn_nccl': docker.get_cuda_cudnn_nccl_choices('chainer'),
    'numpy': docker.get_numpy_choices(),
    'scipy': [None, '0.18'],
    'protobuf': ['2', '3', 'cpp-3'],
    'h5py': [None, '2.5', '2.6', '2.7'],
    'pillow': [None, '3.4', '4.0', '4.1'],
    'theano': [None, '0.8', '0.9'],
    'ideep': [None, '1.0'],
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--id', type=int, required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='2h')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument(
        '--clone-cupy', action='store_true',
        help='clone cupy repository based on chainer version.')

    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if args.clone_cupy:
        version.clone_cupy()

    conf = shuffle.make_shuffle_conf(params, args.id)
    conf['requires'] = [
        'setuptools',
        'pip',
        'cython==0.28.3'
    ] + conf['requires'] + [
        'pytest',
        'pytest-timeout',  # For timeout
        'pytest-cov',  # For coverage report
        'nose',
        'mock',
        'coveralls',
        'codecov',
    ]

    use_ideep = any(['ideep4py' in req for req in conf['requires']])

    volume = []
    env = {
        'CUDNN': conf['cudnn'],
        'IDEEP': 'ideep4py' if use_ideep else 'none',
    }

    argconfig.parse_args(args, env, conf, volume)
    argconfig.setup_coverage(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env)
    else:
        if conf['cuda'] != 'none':
            docker.run_with(
                conf, './test.sh', no_cache=args.no_cache, volume=volume,
                env=env, timeout=args.timeout, gpu_id=args.gpu_id,
                use_root=args.root)
        else:
            docker.run_with(
                conf, './test_cpu.sh', no_cache=args.no_cache, volume=volume,
                env=env, timeout=args.timeout, use_root=args.root)
