import argparse
import os


def setup_argument_parser(parser):
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
