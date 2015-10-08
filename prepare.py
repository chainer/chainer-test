#!/usr/bin/env python

import argparse
import os
import shutil

def copy_file(data_dir, file_name):
    shutil.copy(os.path.join(data_dir, file_name), '.')

p = argparse.ArgumentParser()
p.add_argument('--cuda', choices=['none', 'cuda65', 'cuda70', 'cuda75'], required=True)
p.add_argument('--cudnn', choices=['none', 'cudnn2', 'cudnn3'], required=True)
p.add_argument('-d', '--datadir', default='/opt/cuda')
args = p.parse_args()

if args.cuda == 'cuda65':
    copy_file(args.datadir, 'cuda_6.5.19_linux_64.run')
    copy_file(args.datadir, 'cuda_7.5.18_linux.run')
elif args.cuda == 'cuda70':
    copy_file(args.datadir, 'cuda_7.0.28_linux.run')
    copy_file(args.datadir, 'cuda_7.5.18_linux.run')
elif args.cuda == 'cuda75':
    copy_file(args.datadir, 'cuda_7.5.18_linux.run')

if args.cudnn == 'cudnn2':
    copy_file(args.datadir, 'cudnn-6.5-linux-x64-v2.tgz')
elif args.cudnn == 'cudnn3':
    copy_file(args.datadir, 'cudnn-7.0-linux-x64-v3.0-prod.tgz')

