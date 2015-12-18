#!/usr/bin/env python

import argparse
import os
import shutil


def copy_file(data_dir, file_name):
    shutil.copy(os.path.join(data_dir, file_name), '.')

p = argparse.ArgumentParser()
p.add_argument('--cudnn', choices=['none', 'cudnn2', 'cudnn3'], required=True)
p.add_argument('-d', '--datadir', default='/opt/cuda')
args = p.parse_args()

if args.cudnn == 'cudnn2':
    copy_file(args.datadir, 'cudnn-6.5-linux-x64-v2.tgz')
elif args.cudnn == 'cudnn3':
    copy_file(args.datadir, 'cudnn-7.0-linux-x64-v3.0-prod.tgz')
