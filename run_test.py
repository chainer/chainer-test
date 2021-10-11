#!/usr/bin/env python

import argparse
import os

import argconfig
import docker
import version


# Simulate the build environment of ReadTheDocs (conda).
# Some packages are omitted as we have our own requirements.
# https://github.com/rtfd/readthedocs.org/blob/a992ad1a2695d6d6f2396f67af2163abac2a22d0/readthedocs/doc_builder/python_environments.py#L418
SPHINX_REQUIREMENTS_CONDA = [
    # 'mock',
    # 'pillow',
    'recommonmark',
    'sphinx',
    'sphinx-rtd-theme',
]

# Simulate the build environment of ReadTheDocs (pip).
# Some packages are omitted as we have our own requirements.
# https://github.com/rtfd/readthedocs.org/blob/a992ad1a2695d6d6f2396f67af2163abac2a22d0/readthedocs/doc_builder/python_environments.py#L257
SPHINX_REQUIREMENTS_PIP = [
    'Pygments==2.3.1',
    'docutils==0.14',
    # 'mock==1.0.1',
    # 'pillow==5.4.1',
    'alabaster>=0.7,<0.8,!=0.7.5',
    'commonmark==0.8.1',
    'recommonmark==0.5.0',
    'sphinx<2',
    'sphinx-rtd-theme<2',
]


def _get_job_name():
    # Returns Jenkins job name. None if the test is not running inside Jenkins.
    # e.g., `chainer/cupy_pr/TEST=cupy-py3,label=mn1-p100`
    return os.getenv('JOB_NAME')


def main():
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'chainer-py3', 'chainer-py35', 'chainer-slow',
        'chainer-example', 'chainer-prev_example', 'chainer-doc',
        'chainer-head',
        'cupy-py3', 'cupy-py36', 'cupy-slow', 'cupy-py3-cub', 'cupy-py3-cutensor',
        'cupy-example', 'cupy-doc',
        'cupy-head',
    ], required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='3h')
    parser.add_argument('-i', '--interactive', action='store_true')
    parser.add_argument(
        '--clone-cupy', action='store_true',
        help='clone cupy repository based on chainer version. '
        'this option is used for testing chainer.')
    parser.add_argument(
        '--clone-chainer', action='store_true',
        help='clone chainer repository based on cupy version. '
        'this option is used for testing cupy.')
    parser.add_argument(
        '--env', action='append', default=[],
        help='inherit environment variable (like `docker run --env`)')
    argconfig.setup_argument_parser(parser)
    args = parser.parse_args()

    if args.clone_cupy:
        version.clone_cupy()
    if args.clone_chainer:
        version.clone_chainer()

    is_cupy_master = version.is_master_branch('cupy')
    use_gcc6_or_later = True

    ideep_min_version = version.get_ideep_version_from_chainer_docs()
    if ideep_min_version is None:
        ideep_req = None  # could not determine
    elif ideep_min_version.startswith('1.'):
        ideep_req = '<1.1'
    elif ideep_min_version.startswith('2.'):
        ideep_req = '<2.1'
    else:
        raise RuntimeError('bad ideep version: {}'.format(ideep_min_version))

    build_chainerx = False
    cupy_accelerators = []

    if args.test == 'chainer-py3':
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda101',
            'cudnn': 'cudnn76-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.29.22',
                'numpy==1.19.*', 'pillow',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-py35':
        assert ideep_req is not None
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda92',
            'cudnn': 'cudnn71-cuda92',
            'nccl': 'nccl2.2-cuda92',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22',
                'numpy==1.18.*', 'scipy==1.4.*',
                'h5py', 'theano', 'protobuf<3',
                'ideep4py{}'.format(ideep_req),
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-head' or args.test == 'cupy-head':
        assert ideep_req is not None

        base = 'ubuntu16_py36-pyenv'
        if is_cupy_master:
            base = 'ubuntu16_py37-pyenv'

        conf = {
            'base': base,
            'cuda': 'cuda101',
            'cudnn': 'cudnn76-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # Use '>=0.0.dev0' to install the latest pre-release version
                # available on PyPI.
                # https://pip.pypa.io/en/stable/reference/pip_install/#pre-release-versions
                # TODO(kmaehashi) rewrite iDeep constraints after v2.0 support
                'setuptools>=0.0.dev0', 'cython>=0.0.dev0,<3', 'numpy>=0.0.dev0',
                'scipy>=0.0.dev0', 'h5py>=0.0.dev0', 'theano>=0.0.dev0',
                'protobuf>=0.0.dev0',
                'ideep4py>=0.0.dev0, {}'.format(ideep_req),
            ],
        }
        if args.test == 'chainer-head':
            script = './test.sh'
        elif args.test == 'cupy-head':
            script = './test_cupy.sh'
        else:
            assert False  # should not reach

    elif args.test == 'chainer-slow':
        assert ideep_req is not None

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda92',
            'cudnn': 'cudnn76-cuda92',
            'nccl': 'nccl2.4-cuda92',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22',
                'numpy==1.18.*', 'scipy==1.4.*',
                'scipy<1.1', 'h5py', 'theano', 'protobuf<3', 'pillow',
                'ideep4py{}'.format(ideep_req),
            ],
        }
        script = './test_slow.sh'

    elif args.test == 'chainer-example':
        base = 'ubuntu16_py36-pyenv'
        conf = {
            'base': base,
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda102',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22', 'numpy==1.18.*',
            ],
        }
        script = './test_example.sh'

    elif args.test == 'chainer-prev_example':
        base = 'ubuntu16_py36-pyenv'
        conf = {
            'base': base,
            'cuda': 'cuda92',
            'cudnn': 'cudnn72-cuda92',
            'nccl': 'none',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'pip', 'cython==0.29.22', 'numpy==1.18.*',
            ],
        }
        script = './test_prev_example.sh'

    elif args.test == 'chainer-doc':
        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu16_py36-pyenv',
            'cuda': 'cuda92',
            'cudnn': 'cudnn76-cuda92',
            'nccl': 'none',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'pip==9.0.1', 'setuptools<50', 'cython==0.29.22', 'matplotlib',
                'numpy==1.18.*', 'scipy==1.4.*', 'theano', 'wheel', 'pytest',
            ] + SPHINX_REQUIREMENTS_CONDA
        }
        script = './test_doc.sh'
        build_chainerx = True

    elif args.test == 'cupy-py3':
        requires = ['optuna']
        conf = {
            'base': 'ubuntu18_py39-pyenv',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda102',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                'setuptools<42', 'pip', 'cython==0.29.22',
                'numpy==1.21.*', 'scipy==1.7.*',
            ] + requires,
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3-cutensor':
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda102',
            'cutensor': 'cutensor1.3-cuda102',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.29.22', 'numpy==1.21.*',
            ],
        }
        script = './test_cupy.sh'
        cupy_accelerators += ['cutensor']

    elif args.test == 'cupy-py3-cub':
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda100',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.29.22', 'numpy==1.21.*',
            ],
        }
        script = './test_cupy.sh'
        cupy_accelerators += ['cub']

    elif args.test == 'cupy-py36':
        numpy_requires = 'numpy==1.17.*'
        scipy_requires = 'scipy==1.4.*'

        conf = {
            'base': 'ubuntu18_py36',
            'cuda': 'cuda113',
            'cudnn': 'cudnn82-cuda113',
            'nccl': 'nccl2.9-cuda113',
            'cutensor': 'none',
            'cusparselt': 'cusparselt0.1.0-cuda112',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22',
                numpy_requires, scipy_requires,
            ],
        }
        script = './test_cupy.sh'
        use_gcc6_or_later = True

    elif args.test == 'cupy-slow':
        numpy_requires = 'numpy==1.17.*'
        scipy_requires = 'scipy==1.4.*'

        base = 'ubuntu18_py36'
        if is_cupy_master:
            base = 'ubuntu18_py37-pyenv'

        conf = {
            'base': base,
            'cuda': 'cuda112',
            'cudnn': 'cudnn81-cuda112',
            'nccl': 'none',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22',
                numpy_requires, scipy_requires,
            ],
        }
        script = './test_cupy_slow.sh'

    elif args.test == 'cupy-example':
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda102',
            'cutensor': 'cutensor1.2.0-cuda102',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'setuptools<50', 'cython==0.29.22',
                'numpy==1.19.*', 'scipy==1.6.*',
            ],
        }
        script = './test_cupy_example.sh'

    elif args.test == 'cupy-doc':
        requires = ['optuna<2']

        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda100',
            'cutensor': 'none',
            'cusparselt': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/pypa/setuptools/issues/2352
                'pip==9.0.1', 'setuptools<50', 'cython==0.29.22',
                'numpy==1.21.*', 'scipy==1.7.*', 'wheel==0.36.2'
            ] + requires + SPHINX_REQUIREMENTS_PIP
        }
        script = './test_cupy_doc.sh'

    else:
        raise

    use_ideep = any(['ideep4py' in req for req in conf['requires']])

    volume = []
    env = {
        'USE_GCC6_OR_LATER': '1' if use_gcc6_or_later else '0',
        'CUDNN': conf['cudnn'],
        'IDEEP': 'ideep4py' if use_ideep else 'none',
        'CHAINER_BUILD_CHAINERX': '1' if build_chainerx else '0',
        'CUPY_ACCELERATORS': ','.join(cupy_accelerators),
    }

    argconfig.parse_args(args, env, conf, volume)

    # inherit specified environment variable
    for key in args.env:
        env[key] = os.environ[key]

    # coverage result is reported when the same type of a test is executed
    if args.coverage_repo and args.coverage_repo in args.test:
        argconfig.setup_coverage(args, env)

    if args.interactive:
        docker.run_interactive(
            conf, no_cache=args.no_cache, volume=volume, env=env,
            use_root=args.root)
    else:
        docker.run_with(
            conf, script, no_cache=args.no_cache, volume=volume, env=env,
            timeout=args.timeout, gpu_id=args.gpu_id, use_root=args.root)


if __name__ == '__main__':
    main()
