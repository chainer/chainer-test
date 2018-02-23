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
        '--root', action='store_true',
        help='run the Docker container with a root user.')

    parser.add_argument(
        '--http-proxy',
        help='http proxy server (http://hostname:PORT). '
        'use CHAINER_TEST_HTTP_PROXY environment variable by default.')
    parser.add_argument(
        '--https-proxy',
        help='https proxy server (http://hostname:PORT). '
        'use CHAINER_TEST_HTTPS_PROXY environment variable by default.')

    parser.add_argument(
        '--coverage-repo', choices=['chainer', 'cupy'],
        help='repository to report coverage information. '
        '[chainer, cupy]')
    parser.add_argument(
        '--coveralls-branch',
        help='branch name to report Coveralls. '
        'use ghprbSourceBranch environment varialbe by default. ')
    parser.add_argument(
        '--coveralls-token',
        help='repo token for Coveralls. '
        'use CHAINER_TEST_COVERALLS_XXX_TOKEN environment '
        'variable (where XXX is a uppercased value of --coverage-repo) by '
        'default.')
    parser.add_argument(
        '--codecov-token',
        help='repo token for Codecov. '
        'use CHAINER_TEST_CODECOV_XXX_TOKEN environment '
        'variable (where XXX is a uppercased value of --coverage-repo) by '
        'default.')


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
        env['CUDA_CACHE_PATH'] = os.path.join(cache, '.nv')
        env['CUPY_CACHE_DIR'] = os.path.join(cache, '.cupy')
        env['CCACHE_DIR'] = os.path.join(cache, '.ccache')

    http_proxy = get_arg_value(args, 'http-proxy')
    if http_proxy is not None:
        conf['http_proxy'] = http_proxy

    https_proxy = get_arg_value(args, 'https-proxy')
    if https_proxy is not None:
        conf['https_proxy'] = https_proxy


def setup_coverage(args, env):
    # Set environment variables for Coveralls.
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

    def _get_token(repo, service):
        assert repo in ['chainer', 'cupy']
        assert service in ['coveralls', 'codecov']

        arg_key = '{}-token'.format(service)
        env_key = 'CHAINER_TEST_{}_{}_TOKEN'.format(
            service.upper(), repo.upper())
        repo_token = get_arg_value(args, arg_key, env_key)
        if repo_token is None:
            logging.warning(
                '--coverage-repo={repo} is specified but '
                '--{arg_key} or {env_key} environment variable is not '
                'given'.format(repo=repo, arg_key=arg_key, env_key=env_key))
        return repo_token

    # Set token for Coveralls and Codecov.
    if args.coverage_repo:
        token = _get_token(args.coverage_repo, 'coveralls')
        if token is not None:
            env['COVERALLS_REPO_TOKEN'] = token

        token = _get_token(args.coverage_repo, 'codecov')
        if token is not None:
            env['CODECOV_TOKEN'] = token
