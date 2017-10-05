import os
import re
import subprocess


version_pattern = '([0-9]+)\\.([0-9]+)\\.([0-9]+)([a-z][a-z\\.0-9]+)?'


def get_version(setup_path):
    if not os.path.isfile(setup_path):
        return None
    with open(setup_path) as f:
        for line in f:
            m = re.match(
                ' *version=\'%s\'' % version_pattern,
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


def is_master_branch(directory):
    # A master branch does not have "[backport]" in their logs.
    return_code = subprocess.call(
        'cd %s && git log | grep -q "^ *\\[backport\\]"' % directory,
        shell=True)
    return return_code != 0


def git_clone(organization, name, branch):
    print('cloning %s/%s %s' % (organization, name, branch))
    repository = 'git@github.com:%s/%s.git' % (organization, name)
    subprocess.check_call([
        'git', 'clone', repository, '--depth=1', '-b', branch])


def clone_cupy():
    """Clone cupy repository based on chainer version."""
    if is_master_branch('chainer'):
        cupy_branch = 'master'
    else:
        chainer_major, _, _, _ = get_chainer_version()
        # cupy v(n-1) for chainer v(n)
        cupy_branch = 'v%d' % (chainer_major - 1)
    git_clone('cupy', 'cupy', cupy_branch)


def clone_chainer():
    """Clone cupy repository based on chainer version."""
    if is_master_branch('cupy'):
        chainer_branch = 'master'
    else:
        cupy_major, _, _, _ = get_cupy_version()
        # chainer v(n+1) for cupy v(n)
        chainer_branch = 'v%d' % (cupy_major + 1)
    git_clone('chainer', 'chainer', chainer_branch)
