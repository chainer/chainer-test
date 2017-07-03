#!/usr/bin/env python

import argparse
import os
import sys

import coveralls


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', help='build ID')
    parser.add_argument('--pr', type=int, help='pull request ID on github')
    parser.add_argument('--branch', help='branch name')
    args = parser.parse_args()

    if args.build:
        build = args.build
    elif 'COVERALLS_BUILD' in os.environ:
        build = os.getenv('COVERALLS_BUILD')
    else:
        build = None

    if args.pr:
        pr = args.pr
    elif 'COVERALLS_PR' in os.environ:
        pr = os.getenv('COVERALLS_PR')
    else:
        pr = None

    if args.branch:
        branch = args.branch
    elif 'COVERALLS_BRANCH' in os.environ:
        branch = os.getenv('COVERALLS_BRANCH')
    else:
        branch = None

    kwargs = {}
    if build is not None:
        kwargs['service_number'] = str(build)
    if pr is not None:
        kwargs['service_pull_request'] = str(pr)
    if branch is not None:
        # git.branch cannot be updates with kwargs
        os.environ['CIRCLE_BRANCH'] = branch

    c = coveralls.Coveralls(False, **kwargs)
    res = c.wear()
    print(res['message'])
    print(res['url'])


if __name__ == '__main__':
    main()
