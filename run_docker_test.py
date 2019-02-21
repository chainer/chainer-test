#!/usr/bin/env python

import argparse
import os
import subprocess

import docker


def main():
    parser = argparse.ArgumentParser(
        description='Test script for Dockerfile of Chainer')
    parser.add_argument('--subdir', '-s', choices=['python2', 'python3'],
                        default='python2',
                        help='Sub-directory name ("python2" or "python3")')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run bash instead of test')
    args = parser.parse_args()

    os.chdir('chainer/docker/%s' % args.subdir)
    name = docker.make_random_name()
    docker.build_image(name)
    cmd = [
        'nvidia-docker', 'run', '--rm',
        '-u', str(os.getuid()),
    ]

    if args.interactive:
        cmd += ['-it', name, '/bin/bash']
    else:
        if args.subdir == 'python2':
            python_command = 'python'
        else:
            python_command = 'python3'
        cmd += [
            name, python_command, '-c', 'import cupy; cupy.array([1])',
        ]

    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
