import argparse
import logging
import os


def setup_argument_parser(parser):
    parser.add_argument(
        '--gpu-id', type=int,
        help='GPU ID you want to use mainly in the script.'
        'use EXECUTOR_NUMBER environment variable by default.')
    parser.add_argument(
        '--cache',
        help='cache directory to store cupy cache and ccache. '
        'use CHAINER_TEST_CACHE environment variable by default.')
    parser.add_argument(
        '--http-proxy',
        help='http proxy server (http://hostname:PORT). '
        'use CHAINER_TEST_HTTP_PROXY environment variable by default.')
    parser.add_argument(
        '--https-proxy',
        help='https proxy server (http://hostname:PORT). '
        'use CHAINER_TEST_HTTPS_PROXY environment variable by default.')

    parser.add_argument(
        '--coveralls-repo', choices=['chainer', 'cupy'],
        help='reporsitoy to report coverage information to Coveralls. '
        '[chainer, cupy]')
    parser.add_argument(
        '--coveralls-chainer-token',
        help='repo token of Chainer for Coveralls. '
        'it is used when `--coveralls-repo=chainer` is selected. '
        'use CHAINER_TEST_COVERALLS_CHAINER_TOKEN environment '
        'variable by default.')
    parser.add_argument(
        '--coveralls-cupy-token',
        help='repo token of CuPy for Coveralls. '
        'it is used when `--coveralls-repo=cupy` is selected. '
        'use CHAINER_TEST_COVERALLS_CUPY_TOKEN environment '
        'variable by default.')
    parser.add_argument(
        '--coveralls-branch',
        help='branch name to report Coveralls. '
        'use ghprbSourceBranch environment varialbe by default. '
        'if both are not specified it is ignored.')


def get_arg_value(args, arg_key, env_key=None):
    key = arg_key.replace('-', '_')
    if getattr(args, key) is not None:
        return getattr(args, key)
    else:
        if env_key is None:
            env_key = 'CHAINER_TEST_%s' % (key.upper())
        if env_key in os.environ:
            return os.getenv(env_key)

    return None


def parse_args(args, env, conf, volume):
    gpu_id = get_arg_value(args, 'gpu_id', 'EXECUTOR_NUMBER')
    if gpu_id is not None:
        args.gpu_id = int(gpu_id)

    cache = get_arg_value(args, 'cache')
    if cache is not None:
        volume.append(cache)
        env['CUPY_CACHE_DIR'] = os.path.join(cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(cache, '.ccache')

    http_proxy = get_arg_value(args, 'http-proxy')
    if http_proxy is not None:
        conf['http_proxy'] = http_proxy

    https_proxy = get_arg_value(args, 'https-proxy')
    if https_proxy is not None:
        conf['https_proxy'] = https_proxy


def set_coveralls(args, env):
    if 'BUILD_NUMBER' in os.environ and 'JOB_NAME' in os.environ:
        job = os.getenv('JOB_NAME').split('/')[0]
        build_num = os.getenv('BUILD_NUMBER')
        build = '%s#%s' % (job, build_num)
        env['COVERALLS_BUILD'] = build

    if 'ghprbPullId' in os.environ:
        env['COVERALLS_PR'] = os.getenv('ghprbPullId')
    elif 'PR' in os.environ:
        env['COVERALLS_PR'] = os.getenv('PR')

    if args.coveralls_branch:
        env['COVERALLS_BRANCH'] = args.coveralls_branch
    elif 'ghprbSourceBranch' in os.environ:
        branch = os.getenv('ghprbSourceBranch')
        env['COVERALLS_BRANCH'] = branch

    if args.coveralls_repo == 'chainer':
        repo_token = get_arg_value(args, 'coveralls-chainer-token')
        if repo_token is None:
            logging.warning(
                '--coveralls-repo=chainer is specified but '
                '--coveralls-chainer-token is not given')
        else:
            env['COVERALLS_REPO_TOKEN'] = repo_token
    if args.coveralls_repo == 'cupy':
        repo_token = get_arg_value(args, 'coveralls-cupy-token')
        if repo_token is None:
            logging.warning(
                '--coveralls-repo=cupy is specified but '
                '--coveralls-cupy-token is not given')
        else:
            env['COVERALLS_REPO_TOKEN'] = repo_token
