#!/usr/bin/env python

import argparse
import os

import docker
import version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--base', choices=docker.base_choices_all, required=True)
    parser.add_argument('--cuda', choices=docker.cuda_choices, required=True)
    parser.add_argument('--cudnn', choices=docker.cudnn_choices, required=True)
    parser.add_argument('--nccl', choices=docker.nccl_choices, required=True)
    parser.add_argument('--cutensor', choices=docker.cutensor_choices, required=True)
    parser.add_argument('--cusparselt', choices=docker.cusparselt_choices, required=True)
    parser.add_argument('--ideep', choices=['none', '1.0', '2.0'], required=True)
    parser.add_argument('--numpy',
                        choices=['1.9', '1.10', '1.11', '1.12', '1.13', '1.14', '1.15', '1.16', '1.17'],
                        required=True)
    parser.add_argument('--scipy', choices=['none', '0.18', '0.19', '1.0', '1.4'])
    parser.add_argument('--protobuf', choices=['2', '3', 'cpp-3'])
    parser.add_argument('--h5py', choices=['none', '2.5', '2.6', '2.7', '2.8', '2.9', '2.10'])
    parser.add_argument('--pillow', choices=['none', '3.4', '4.0', '4.1', '6.2'])
    parser.add_argument('--theano', choices=['none', '0.8', '0.9', '1.0'])
    parser.add_argument('--type', choices=['cpu', 'gpu'], required=True)
    parser.add_argument('--cache')
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='2h')
    parser.add_argument(
        '--gpu-id', type=int,
        help='GPU ID you want to use mainly in the script.')
    parser.add_argument('--interactive', action='store_true')
    parser.add_argument(
        '--clone-cupy', action='store_true',
        help='clone cupy repository based on chainer version. '
        'this option is used for testing chainer.')
    parser.add_argument(
        '--clone-chainer', action='store_true',
        help='clone chainer repository based on cupy version. '
        'this option is used for testing cupy.')
    args = parser.parse_args()

    if args.clone_cupy:
        version.clone_cupy()
    if args.clone_chainer:
        version.clone_chainer()

    conf = {
        'base': args.base,
        'cuda': args.cuda,
        'cudnn': args.cudnn,
        'nccl': args.nccl,
        'cutensor': args.cutensor,
        'cusparselt': args.cusparselt,
        'requires': ['setuptools', 'pip', 'cython==0.29.22'],
    }

    if args.h5py == '2.5':
        conf['requires'].append('numpy<1.10')
        conf['requires'].append('h5py<2.6')
    elif args.h5py == '2.6':
        conf['requires'].append('h5py<2.7')
    elif args.h5py == '2.7':
        conf['requires'].append('h5py<2.8')
    elif args.h5py == '2.8':
        conf['requires'].append('h5py<2.9')
    elif args.h5py == '2.9':
        conf['requires'].append('h5py<2.10')
    elif args.h5py == '2.10':
        conf['requires'].append('h5py<2.11')

    if args.theano == '0.8':
        conf['requires'].append('theano<0.9')
    elif args.theano == '0.9':
        conf['requires'].append('theano<0.10')
    elif args.theano == '1.0':
        conf['requires'].append('theano<1.1')

    if args.numpy == '1.9':
        conf['requires'].append('numpy<1.10')
    elif args.numpy == '1.10':
        conf['requires'].append('numpy<1.11')
    elif args.numpy == '1.11':
        conf['requires'].append('numpy<1.12')
    elif args.numpy == '1.12':
        conf['requires'].append('numpy<1.13')
    elif args.numpy == '1.13':
        conf['requires'].append('numpy<1.14')
    elif args.numpy == '1.14':
        conf['requires'].append('numpy<1.15')
    elif args.numpy == '1.15':
        conf['requires'].append('numpy<1.16')
    elif args.numpy == '1.16':
        conf['requires'].append('numpy<1.17')
    elif args.numpy == '1.17':
        conf['requires'].append('numpy<1.18')

    if args.scipy == '0.18':
        conf['requires'].append('scipy<0.19')
    elif args.scipy == '0.19':
        conf['requires'].append('scipy<0.20')
    elif args.scipy == '1.0':
        conf['requires'].append('scipy<1.1')
    elif args.scipy == '1.4':
        conf['requires'].append('scipy<1.5')

    if args.protobuf == '3':
        conf['requires'].append('protobuf<4')
    elif args.protobuf == '2':
        conf['requires'].append('protobuf<3')
    elif args.protobuf == 'cpp-3':
        conf['protobuf-cpp'] = 'protobuf-cpp-3'

    if args.pillow == '3.4':
        conf['requires'].append('pillow<3.5')
    elif args.pillow == '4.0':
        conf['requires'].append('pillow<4.1')
    elif args.pillow == '4.1':
        conf['requires'].append('pillow<4.2')
    elif args.pillow == '6.2':
        conf['requires'].append('pillow<6.3')

    if args.ideep == '1.0':
        conf['requires'].append('ideep4py<1.1')
    elif args.ideep == '2.0':
        conf['requires'].append('ideep4py<2.1')

    use_ideep = any(['ideep4py' in req for req in conf['requires']])

    volume = []
    env = {
        'CUDNN': conf['cudnn'],
        'IDEEP': 'ideep4py' if use_ideep else 'none',
    }

    if args.cache:
        volume.append(args.cache)
        env['CUDA_CACHE_PATH'] = os.path.join(args.cache, '.nv')
        env['CUPY_CACHE_DIR'] = os.path.join(args.cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(args.cache, '.ccache')

    if args.type == 'cpu':
        script = './test_cpu.sh'
    elif args.type == 'gpu':
        script = './test.sh'
        conf['requires'].append('cupy')

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
