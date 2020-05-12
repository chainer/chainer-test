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
    return os.getenv('JOB_NAME')


def main():
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'chainer-py3', 'chainer-py35', 'chainer-slow',
        'chainer-example', 'chainer-prev_example', 'chainer-doc',
        'chainer-head',
        'cupy-py3', 'cupy-py35', 'cupy-slow', 'cupy-py3-cub', 'cupy-py3-cutensor',
        'cupy-example', 'cupy-doc',
        'cupy-head',
    ], required=True)
    parser.add_argument('--no-cache', action='store_true')
    parser.add_argument('--timeout', default='2h')
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

    is_cupy_8_or_later = (
        version.get_cupy_version() >= (8,) or
        # is_master_branch() is required because v8 beta branch has v7 as
        # the version number in _version.py.
        # After releasing v8 as stable, remove this condition.
        version.is_master_branch('cupy'))

    skip_chainer_test = _get_job_name() == 'cupy_pr' and is_cupy_8_or_later

    if not is_cupy_8_or_later:
        numpy_min_version = '1.9'
        numpy_newest_upper_version = '1.18'
        scipy_min_version = '0.18'
        scipy_newest_upper_version = '1.5'
    else:
        numpy_min_version = '1.15'
        numpy_newest_upper_version = '1.19'
        scipy_min_version = '1.1'
        scipy_newest_upper_version = '1.5'

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
    use_cub = False
    if args.test == 'chainer-py3':
        if skip_chainer_test:
            print('Skipping chainer test for CuPy>=8')
            return

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda101',
            'cudnn': 'cudnn75-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'cutensor': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.29.13',
                numpy_requires, 'pillow',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-py35':
        assert ideep_req is not None
        if skip_chainer_test:
            print('Skipping chainer test for CuPy>=8')
            return

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_newest_upper_version)
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda92',
            'cudnn': 'cudnn71-cuda92',
            'nccl': 'nccl2.2-cuda92',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
                'h5py', 'theano', 'protobuf<3',
                'ideep4py{}'.format(ideep_req),
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-head' or args.test == 'cupy-head':
        assert ideep_req is not None
        conf = {
            'base': 'ubuntu16_py36-pyenv',
            'cuda': 'cuda101',
            'cudnn': 'cudnn75-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'cutensor': 'none',
            'requires': [
                # Use '>=0.0.dev0' to install the latest pre-release version
                # available on PyPI.
                # https://pip.pypa.io/en/stable/reference/pip_install/#pre-release-versions
                # TODO(kmaehashi) rewrite iDeep constraints after v2.0 support
                'setuptools>=0.0.dev0', 'cython>=0.0.dev0', 'numpy>=0.0.dev0',
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

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_newest_upper_version)
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
                'scipy<1.1', 'h5py', 'theano', 'protobuf<3', 'pillow',
                'ideep4py{}'.format(ideep_req),
            ],
        }
        script = './test_slow.sh'

    elif args.test == 'chainer-example':
        if skip_chainer_test:
            print('Skipping chainer test for CuPy>=8')
            return

        base = 'ubuntu16_py35'
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': base,
            'cuda': 'cuda90',
            'cudnn': 'cudnn73-cuda9',
            'nccl': 'nccl2.2-cuda9',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13', numpy_requires,
            ],
        }
        script = './test_example.sh'

    elif args.test == 'chainer-prev_example':
        if skip_chainer_test:
            print('Skipping chainer test for CuPy>=8')
            return

        base = 'ubuntu16_py35'
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': base,
            'cuda': 'cuda92',
            'cudnn': 'cudnn72-cuda92',
            'nccl': 'none',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.29.13', numpy_requires,
            ],
        }
        script = './test_prev_example.sh'

    elif args.test == 'chainer-doc':
        if skip_chainer_test:
            print('Skipping chainer test for CuPy>=8')
            return

        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        numpy_requires = 'numpy>={},<{}'.format(
            '1.15', numpy_newest_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_newest_upper_version)
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'cutensor': 'none',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.29.13', 'matplotlib',
                numpy_requires, scipy_requires, 'theano',
            ] + SPHINX_REQUIREMENTS_CONDA
        }
        script = './test_doc.sh'
        build_chainerx = True

    elif args.test == 'cupy-py3':
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda100',
            'cudnn': 'cudnn75-cuda100',
            'nccl': 'nccl2.4-cuda100',
            'cutensor': 'none',
            'requires': [
                'setuptools<42', 'pip', 'cython==0.28.0',
                'numpy>={},<1.18'.format(numpy_min_version),
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3-cutensor':
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda100',
            'cudnn': 'cudnn75-cuda100',
            'nccl': 'nccl2.4-cuda100',
            'cutensor': 'cutensor1.0.1-cuda10',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.28.0', numpy_requires
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3-cub':
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_newest_upper_version)
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda100',
            'cudnn': 'cudnn75-cuda100',
            'nccl': 'nccl2.4-cuda100',
            'cutensor': 'none',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                # https://github.com/chainer/chainer-test/issues/565
                'setuptools<42', 'pip', 'cython==0.28.0', numpy_requires
            ],
        }
        script = './test_cupy.sh'
        use_cub = True

    elif args.test == 'cupy-py35':
        if not is_cupy_8_or_later:
            numpy_upper_version = '1.10'
            scipy_upper_version = '0.19'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
            scipy_upper_version = '1.2'

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_upper_version)

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda102',
            'cudnn': 'cudnn76-cuda102',
            'nccl': 'nccl2.5-cuda102',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-slow':
        if not is_cupy_8_or_later:
            numpy_upper_version = '1.11'
            scipy_upper_version = '0.19'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
            scipy_upper_version = '1.2'

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_upper_version)

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
            ],
        }
        script = './test_cupy_slow.sh'

    elif args.test == 'cupy-example':
        if not is_cupy_8_or_later:
            numpy_upper_version = '1.13'
            scipy_upper_version = '0.19'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
            scipy_upper_version = '1.2'

        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, scipy_upper_version)

        base = 'ubuntu16_py35'
        conf = {
            'base': base,
            'cuda': 'cuda80',
            'cudnn': 'cudnn5-cuda8',
            'nccl': 'nccl1.3',
            'cutensor': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
            ],
        }
        script = './test_cupy_example.sh'

    elif args.test == 'cupy-doc':
        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        numpy_requires = 'numpy>={},<{}'.format(
            '1.15', numpy_newest_upper_version)
        scipy_requires = 'scipy>={},<{}'.format(
            scipy_min_version, '1.4')
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'cutensor': 'none',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.29.13',
                numpy_requires, scipy_requires,
            ] + SPHINX_REQUIREMENTS_PIP
        }
        script = './test_cupy_doc.sh'

    else:
        raise

    use_ideep = any(['ideep4py' in req for req in conf['requires']])

    volume = []
    env = {
        'CUDNN': conf['cudnn'],
        'IDEEP': 'ideep4py' if use_ideep else 'none',
        'CHAINER_BUILD_CHAINERX': '1' if build_chainerx else '0',
        'CUB_DISABLED': '0' if use_cub else '1',
    }
    conf['requires'] += [
        'attrs<19.2.0',
        'pytest<4.2',
        'pytest-timeout',  # For timeout
        'pytest-cov',  # For coverage report
        'nose',
        'mock',
        # coverage 5.0 causes error:
        # "ModuleNotFoundError: No module named '_sqlite3'"
        'coverage<5',
        'coveralls',
        'codecov',
    ]

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
