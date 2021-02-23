#!/usr/bin/env python

import argparse

import argconfig
import docker
import shuffle
import version


ideep_min_version = version.get_ideep_version_from_chainer_docs()
assert ideep_min_version is not None


params = {
    'base': None,
    'cuda_libs': docker.get_cuda_libs_choices('chainer'),
    'numpy': docker.get_numpy_choices(),
    'scipy': docker.get_scipy_choices(),
    'protobuf': ['3', 'cpp-3'],
    'h5py': [None, '2.5', '2.6', '2.7', '2.8', '2.9', '2.10'],
    'pillow': [None, '3.4', '4.0', '4.1', '6.2'],
    'theano': [None, '0.8', '0.9', '1.0'],
    'ideep': [
        None,
        ideep_min_version[:3],  # 'major.minor'
    ],
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

    if version.is_master_branch('chainer'):
        params['base'] = docker.base_choices_master_chainer
    else:
        params['base'] = docker.base_choices_stable_chainer

    if args.clone_cupy:
        version.clone_cupy()

    conf = shuffle.make_shuffle_conf(params, args.id)

    # pip has dropped Python 3.4 support since 19.2.
    # TODO(niboshi): More generic and elegant approach to handle special requirements.
    pip_require = 'pip<19.2' if docker.get_python_version(conf['base'])[:2] == (3, 4) else 'pip'

    conf['requires'] = [
        'setuptools',
        pip_require,
        'cython==0.29.22'
    ] + conf['requires']

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
