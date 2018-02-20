#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse

from az_utils import get_vm_ip
from az_utils import run_on_vm

CHAINER_TEST_REPO = 'https://github.com/mitmul/chainer-test.git'
CHAINER_TEST_BRANCH = 'jenkins-script'
CHAINRE_REPO = 'https://github.com/chainer/chainer.git'
CHAINER_BRANCH = 'master'
CACHE_DIR_ON_SLAVE = '/cache'
RESOURCE_GROUP = 'chainer-jenkins'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build_id', type=str)
    parser.add_argument('--test', type=str)
    parser.add_argument('--vm_name', type=str)
    parser.add_argument('--coveralls_token', type=str)
    args = parser.parse_args()

    cmd = """ \
    if [ ! -d {test} ]; then mkdir {test}; fi && \
    cd {test} && \
    mkdir \#{build_id} && \
    cd \#{build_id} && \
    git clone -b {chainer_test_branch} {chainer_test_repo} && \
    cd chainer-test && \
    git clone -b {chainer_branch} {chainer_repo} && \
    ./run_test.py --test {test} \
    --cache {cache_dir_on_slave} \
    --coveralls-repo=chainer \
    --coveralls-branch=master \
    --coveralls-chainer-token {coveralls_token} \
    --clone-cupy
    """.format(
        build_id=args.build_id,
        test=args.test,
        chainer_test_branch=CHAINER_TEST_BRANCH,
        chainer_test_repo=CHAINER_TEST_REPO,
        chainer_branch=CHAINER_BRANCH,
        chainer_repo=CHAINRE_REPO,
        cache_dir_on_slave=CACHE_DIR_ON_SLAVE,
        coveralls_token=args.coveralls_token
    )
    print(cmd)
    run_on_vm(args.vm_name, cmd)


if __name__ == '__main__':
    main()
