#!/usr/bin/env python

import argparse

codes = {}

# base

codes['centos7_py2'] = '''FROM centos:7

RUN yum -y update
RUN yum -y install epel-release
RUN yum -y install gcc gcc-c++ kmod libhdf5-devel perl python-devel python-pip
'''

codes['ubuntu14_py2'] = '''FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y curl g++ gfortran libhdf5-dev python-pip python-dev
'''

codes['ubuntu14_py3'] = '''FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y curl g++ gfortran libhdf5-dev python3-pip python3-dev

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
'''

# numpy

codes['numpy19'] = '''
RUN pip install numpy==1.9.3
'''

codes['numpy110'] = '''
RUN pip install numpy==1.10
'''

# cuda

cuda65_run = 'cuda_6.5.19_linux_64.run'
cuda65_url = 'http://developer.download.nvidia.com/compute/cuda/6_5/rel/installers'
cuda65_installer = 'cuda-linux64-rel-6.5.19-18849900.run'

cuda70_run = 'cuda_7.0.28_linux.run'
cuda70_url = 'http://developer.download.nvidia.com/compute/cuda/7_0/Prod/local_installers'
cuda70_installer = 'cuda-linux64-rel-7.0.28-19326674.run'

cuda75_run = 'cuda_7.5.18_linux.run'
cuda75_url = 'http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers'
cuda75_driver = 'NVIDIA-Linux-x86_64-352.39.run'
cuda75_installer = 'cuda-linux64-rel-7.5.18-19867135.run'

cuda_base = '''
WORKDIR /opt/nvidia
ENV CUDA_RUN {cuda_run}
ENV CUDA_75_RUN {cuda75_run}

COPY $CUDA_RUN /opt/nvidia/
COPY $CUDA_75_RUN /opt/nvidia/

RUN mkdir installers
RUN chmod +x $CUDA_RUN && sync && \\
    ./$CUDA_RUN -extract=`pwd`/installers
RUN chmod +x $CUDA_75_RUN && sync && \\
    ./$CUDA_75_RUN -extract=`pwd`/installers

RUN cd installers && \\
    ./{driver} -s -N --no-kernel-module && \\
    ./{installer} -noprompt && \\
    cd / && \\
    rm -rf /opt/nvidia

ENV CUDA_ROOT /usr/local/cuda
ENV PATH $PATH:$CUDA_ROOT/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_ROOT/lib64
'''

cuda75_base = '''
WORKDIR /opt/nvidia
ENV CUDA_RUN {cuda_run}

COPY $CUDA_RUN /opt/nvidia/

RUN mkdir installers
RUN chmod +x $CUDA_RUN && sync && \\
    ./$CUDA_RUN -extract=`pwd`/installers

RUN cd installers && \\
    ./{driver} -s -N --no-kernel-module && \\
    ./{installer} -noprompt && \\
    cd / && \\
    rm -rf /opt/nvidia

ENV CUDA_ROOT /usr/local/cuda
ENV PATH $PATH:$CUDA_ROOT/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_ROOT/lib64
'''

codes['cuda65'] = cuda_base.format(
    cuda_run=cuda65_run,
    cuda_url=cuda65_url,
    cuda75_run=cuda75_run,
    cuda75_url=cuda75_url,
    driver=cuda75_driver,
    installer=cuda65_installer,
)

codes['cuda70'] = cuda_base.format(
    cuda_run=cuda70_run,
    cuda_url=cuda70_url,
    cuda75_run=cuda75_run,
    cuda75_url=cuda75_url,
    driver=cuda75_driver,
    installer=cuda70_installer,
)

codes['cuda75'] = cuda75_base.format(
    cuda_run=cuda75_run,
    cuda_url=cuda75_url,
    driver=cuda75_driver,
    installer=cuda75_installer,
)

# cudnn

cudnn_base = '''
WORKDIR /opt/cudnn
ENV CUDNN {cudnn}
ADD $CUDNN.tgz /opt/cudnn/
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:/opt/cudnn/$CUDNN
'''

codes['cudnn2'] = cudnn_base.format(cudnn='cudnn-6.5-linux-x64-v2')
codes['cudnn3'] = cudnn_base.format(cudnn='cudnn-7.0-linux-x64-v3.0-prod')

codes['none'] = ''

p = argparse.ArgumentParser()
p.add_argument('--base', choices=['ubuntu14_py2', 'ubuntu14_py3', 'centos7_py2'], required=True)
p.add_argument('--numpy', choices=['numpy19', 'numpy110'], required=True)
p.add_argument('--cuda', choices=['none', 'cuda65', 'cuda70', 'cuda75'], required=True)
p.add_argument('--cudnn', choices=['none', 'cudnn2', 'cudnn3'], required=True)
p.add_argument('-f', '--dockerfile', default='Dockerfile')
args = p.parse_args()

with open(args.dockerfile, 'w') as f:
    f.write(codes[args.base])
    f.write(codes[args.numpy])
    f.write(codes[args.cuda])
    f.write(codes[args.cudnn])