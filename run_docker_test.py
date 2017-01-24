#!/usr/bin/env python2

import argparse
import os
import subprocess

import docker


def main():
    parser = argparse.ArgumentParser(
        description='Test script for Dockerfile of Chainer')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Run bash instead of test')
    args = parser.parse_args()

    os.chdir('chainer/docker')
    name = docker.make_random_name()
    docker.build_image(name)
    cmd = [
        'nvidia-docker', 'run', '--rm',
        '-u', str(os.getuid()),
    ]

    if args.interactive:
        cmd += ['-it', name, '/bin/bash']
    else:
        cmd += [
            name, 'python', '-c', 'import cupy; cupy.array([1])',
        ]

    subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
