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
        'chainer-py2', 'chainer-py3', 'chainer-py35', 'chainer-slow',
        'chainer-example', 'chainer-prev_example', 'chainer-doc',
        'chainer-head',
        'cupy-py2', 'cupy-py3', 'cupy-py35', 'cupy-slow',
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

    support_py2 = not (version.is_master_branch('chainer') or
                       version.is_master_branch('cupy'))

    if version.get_cupy_version() < (8,):
        numpy_min_version = '1.9'
    else:
        numpy_min_version = '1.15'

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
    if args.test == 'chainer-py2':
        if not support_py2:
            print('Skipping Py2 test for master branch')
            return
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        conf = {
            'base': 'ubuntu16_py27',
            'cuda': 'cuda80',
            'cudnn': 'cudnn51-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'setuptools<45',  # 45 dropped python 2
                'pip', 'cython==0.28.0',
                'numpy>={},<1.10'.format(numpy_min_version),
                'scipy<0.19', 'h5py', 'theano', 'pillow',
                'protobuf',  # ignore broken protobuf 3.2.0rc1
            ]
        }
        script = './test.sh'

    elif args.test == 'chainer-py3':
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda101',
            'cudnn': 'cudnn75-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                'setuptools<42', 'pip', 'cython==0.29.13',
                'numpy>={},<1.18'.format(numpy_min_version),
                'pillow',
            ],
        }
        script = './test.sh'

    elif args.test == 'chainer-py35':
        assert ideep_req is not None
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda92',
            'cudnn': 'cudnn71-cuda92',
            'nccl': 'nccl2.2-cuda92',
            'requires': [
                'setuptools', 'cython==0.29.13',
                'numpy>={},<1.14'.format(numpy_min_version),
                'scipy<1.1', 'h5py', 'theano', 'protobuf<3',
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
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'setuptools', 'cython==0.29.13',
                'numpy>={},<1.16'.format(numpy_min_version),
                'scipy<1.1', 'h5py', 'theano', 'protobuf<3',
                'pillow',
                'ideep4py{}'.format(ideep_req),
            ],
        }
        script = './test_slow.sh'

    elif args.test == 'chainer-example':
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        base = 'centos7_py27' if support_py2 else 'ubuntu16_py35'
        conf = {
            'base': base,
            'cuda': 'cuda90',
            'cudnn': 'cudnn73-cuda9',
            'nccl': 'nccl2.2-cuda9',
            'requires': [
                'setuptools', 'cython==0.29.13',
                'numpy>={},<1.13'.format(numpy_min_version),
            ],
        }
        script = './test_example.sh'

    elif args.test == 'chainer-prev_example':
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        base = 'ubuntu16_py27' if support_py2 else 'ubuntu16_py35'
        conf = {
            'base': base,
            'cuda': 'cuda92',
            'cudnn': 'cudnn72-cuda92',
            'nccl': 'none',
            'requires': [
                'setuptools', 'pip', 'cython==0.29.13',
                'numpy>={},<1.12'.format(numpy_min_version),
            ],
        }
        script = './test_prev_example.sh'

    elif args.test == 'chainer-doc':
        if _get_job_name() == 'cupy_pr' and version.get_cupy_version() >= (8,):
            print('Skipping chainer test for CuPy>=8')
            return

        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.29.13', 'matplotlib',
                'numpy>=1.15', 'scipy>=1.0', 'theano',
            ] + SPHINX_REQUIREMENTS_CONDA
        }
        script = './test_doc.sh'
        build_chainerx = True

    elif args.test == 'cupy-py2':
        if not support_py2:
            print('Skipping Py2 test for master branch')
            return

        conf = {
            'base': 'ubuntu16_py27',
            'cuda': 'cuda80',
            'cudnn': 'cudnn51-cuda8',
            'nccl': 'none',
            'requires': [
                'setuptools<45',  # 45 dropped python 2
                'pip', 'cython==0.29.13',
                'numpy>={},<1.16'.format(numpy_min_version),
                'scipy<1.1',
            ]
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py3':
        conf = {
            'base': 'ubuntu18_py38-pyenv',
            'cuda': 'cuda100',
            'cudnn': 'cudnn75-cuda100',
            'nccl': 'nccl2.4-cuda100',
            'requires': [
                # TODO(kmaehashi): Remove setuptools version restrictions
                'setuptools<42', 'pip', 'cython==0.28.0',
                'numpy>={},<1.18'.format(numpy_min_version),
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-py35':
        if version.get_cupy_version() < (8,):
            numpy_upper_version = '1.10'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda101',
            'cudnn': 'cudnn75-cuda101',
            'nccl': 'nccl2.4-cuda101',
            'requires': [
                'setuptools', 'cython==0.29.13', numpy_requires, 'scipy<0.19',
            ],
        }
        script = './test_cupy.sh'

    elif args.test == 'cupy-slow':
        if version.get_cupy_version() < (8,):
            numpy_upper_version = '1.11'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)

        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'none',
            'requires': [
                'setuptools', 'cython==0.29.13', numpy_requires, 'scipy<0.19',
            ],
        }
        script = './test_cupy_slow.sh'

    elif args.test == 'cupy-example':
        if version.get_cupy_version() < (8,):
            numpy_upper_version = '1.13'
        else:
            # CuPy v8 dropped NumPy<1.15
            numpy_upper_version = '1.16'
        numpy_requires = 'numpy>={},<{}'.format(
            numpy_min_version, numpy_upper_version)

        base = 'centos7_py27' if support_py2 else 'ubuntu16_py35'
        conf = {
            'base': base,
            'cuda': 'cuda80',
            'cudnn': 'cudnn5-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'setuptools', 'cython==0.29.13', numpy_requires, 'scipy<0.19',
            ],
        }
        script = './test_cupy_example.sh'

    elif args.test == 'cupy-doc':
        # Note that NumPy 1.14 or later is required to run doctest, as
        # the document uses new textual representation of arrays introduced in
        # NumPy 1.14.
        conf = {
            'base': 'ubuntu16_py35',
            'cuda': 'cuda80',
            'cudnn': 'cudnn6-cuda8',
            'nccl': 'nccl1.3',
            'requires': [
                'pip==9.0.1', 'setuptools', 'cython==0.29.13', 'numpy>=1.15',
                # scipy 1.4 causes error during installation.
                'scipy>=1.0,<1.4',
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
