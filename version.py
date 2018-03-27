import imp
import os
import re
import subprocess


version_pattern = '([0-9]+)\\.([0-9]+)\\.([0-9]+)([a-z][a-z\\.0-9]+)?'


def parse_version(version):
    m = re.match(version_pattern, version)
    if m:
        major = int(m.group(1))
        minor = int(m.group(2))
        revision = int(m.group(3))
        pre = m.group(4)
        return major, minor, revision, pre
    else:
        return None


def get_version_from_setup(setup_path):
    if not os.path.isfile(setup_path):
        return None
    with open(setup_path) as f:
        for line in f:
            m = re.match(' *version=\'(.*)\'', line)
            if not m:
                continue
            version = m.group(1)
            version_tuple = parse_version(version)
            if version_tuple is None:
                raise RuntimeError(
                    'cannot parse version: %s (%s)' % (version, setup_path))
            return version_tuple
    raise RuntimeError('version information is not fouond: %s' % setup_path)


def get_version_from_version_file(version_file_path):
    version = imp.load_source(
        '_version', version_file_path).__version__
    version_tuple = parse_version(version)
    if version_tuple is None:
        raise RuntimeError(
            'cannot parse version: %s (%s)' % (version, version_file_path))
    return version_tuple


def get_version(path, module):
    version_path = os.path.join(path, module, '_version.py')
    if os.path.exists(version_path):
        return get_version_from_version_file(version_path)
    else:
        # Old version cupy does not have '_verison.py' and instead version
        # is written in setup.py directrly.
        # TODO(unno): Remove this code when all versions of chainer/cupy
        #   use '_version.py'.
        setup_path = os.path.join(path, 'setup.py')
        return get_version_from_setup(setup_path)


def get_chainer_version():
    chainer_path = os.path.join(os.path.dirname(__file__), 'chainer')
    return get_version(chainer_path, 'chainer')


def get_cupy_version():
    cupy_path = os.path.join(os.path.dirname(__file__), 'cupy')
    return get_version(cupy_path, 'cupy')


def is_master_branch(directory):
    # A master branch does not have "[backport]" in their logs.
    return_code = subprocess.call(
        'cd %s && git log | grep -q "^ *\\[backport\\]"' % directory,
        shell=True)
    return return_code != 0


def git_clone(organization, name, branch):
    print('cloning %s/%s %s' % (organization, name, branch))
    repository = 'https://github.com/%s/%s.git' % (organization, name)
    subprocess.check_call([
        'git', 'clone', repository, '--depth=1', '-b', branch])


def clone_cupy():
    """Clone cupy repository based on chainer version."""
    if is_master_branch('chainer'):
        cupy_branch = 'master'
    else:
        chainer_major, _, _, _ = get_chainer_version()
        if 4 <= chainer_major:
            cupy_branch = 'v%d' % chainer_major
        else:
            # cupy v(n-1) for chainer v(n)
            cupy_branch = 'v%d' % (chainer_major - 1)
    git_clone('cupy', 'cupy', cupy_branch)


def clone_chainer():
    """Clone chainer repository based on cupy version."""
    if is_master_branch('cupy'):
        chainer_branch = 'master'
    else:
        cupy_major, _, _, _ = get_cupy_version()
        if 4 <= cupy_major:
            chainer_branch = 'v%d' % cupy_major
        else:
            # chainer v(n+1) for cupy v(n)
            chainer_branch = 'v%d' % (cupy_major + 1)
    git_clone('chainer', 'chainer', chainer_branch)
