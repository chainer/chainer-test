import os
import re


def get_version(setup_path):
    with open(setup_path) as f:
        for line in f:
            m = re.match(
                ' *version=\'([0-9]+)\\.([0-9]+)\\.([0-9]+)([a-c][0-9]?)?\'',
                line)
            if m:
                major = int(m.group(1))
                minor = int(m.group(2))
                revision = int(m.group(3))
                pre = m.group(4)
                return major, minor, revision, pre
    raise RuntimeError('version information is not fouond: %s' % setup_path)


def get_chainer_version():
    setup_path = os.path.join(os.path.dirname(__file__), 'chainer', 'setup.py')
    return get_version(setup_path)


def get_cupy_version():
    setup_path = os.path.join(os.path.dirname(__file__), 'cupy', 'setup.py')
    return get_version(setup_path)
