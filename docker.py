import logging
import os
import random
import signal
import string
import subprocess
import sys

import version


_base_choices = [
    ('ubuntu14_py27', '2.7.6'),
    ('ubuntu14_py34', '3.4.0'),
    ('ubuntu14_py35-pyenv', '3.5.5'),
    ('ubuntu14_py36-pyenv', '3.6.5'),
    ('ubuntu16_py27', '2.7.12'),
    ('ubuntu16_py35', '3.5.2'),
    ('centos6_py27-pyenv', '2.7.14'),
    ('centos7_py27', '2.7.5'),
    ('centos7_py34-pyenv', '3.4.8')]

base_choices = [a[0] for a in _base_choices]
cuda_choices = ['none', 'cuda70', 'cuda75', 'cuda80', 'cuda90', 'cuda91', 'cuda92']
cudnn_choices = [
    'none', 'cudnn4', 'cudnn5', 'cudnn5-cuda8', 'cudnn51',
    'cudnn51-cuda8', 'cudnn6', 'cudnn6-cuda8', 'cudnn7-cuda8', 'cudnn7-cuda9',
    'cudnn7-cuda91', 'cudnn71-cuda8', 'cudnn71-cuda9', 'cudnn71-cuda91',
    'cudnn71-cuda92']
nccl_choices = [
    'none', 'nccl1.3', 'nccl2.0-cuda8', 'nccl2.0-cuda9', 'nccl2.2-cuda9'
    'nccl2.1-cuda91', 'nccl2.2-cuda92',
]

cuda_cudnns = {
    'cuda70': ['cudnn4'],
    'cuda75': ['cudnn4', 'cudnn5', 'cudnn51', 'cudnn6'],
    'cuda80': ['cudnn5-cuda8', 'cudnn51-cuda8', 'cudnn6-cuda8',
               'cudnn7-cuda8', 'cudnn71-cuda8'],
    'cuda90': ['cudnn7-cuda9', 'cudnn71-cuda9'],
    'cuda91': ['cudnn7-cuda91', 'cudnn71-cuda91'],
    'cuda92': ['cudnn71-cuda92'],
}
cuda_nccls = {
    'cuda70': ['nccl1.3'],
    'cuda75': ['nccl1.3'],
    'cuda80': ['nccl1.3', 'nccl2.0-cuda8'],
    # CUDA 9 does not support nccl 1.3
    'cuda90': ['nccl2.0-cuda9', 'nccl2.2-cuda9'],
    'cuda91': ['nccl2.1-cuda91'],
    'cuda92': ['nccl2.2-cuda92'],
}


def get_python_version(base):
    """Returns the python version to be installed in a tuple."""
    ver = next(a[1] for a in _base_choices if a[0] == base)
    return tuple([int(s) for s in ver.split('.')])


def get_cuda_cudnn_nccl_choices(target, with_dummy=False):
    assert target in ['chainer', 'cupy']

    cupy_version = version.get_cupy_version()
    if cupy_version is not None:
        cupy_major = cupy_version[0]
    else:
        cupy_major = -1

    choices = []
    for cuda in cuda_choices:
        if cuda == 'none':
            continue
        cudnns = ['none'] + cuda_cudnns[cuda]
        nccls = ['none'] + cuda_nccls[cuda]
        if cupy_major < 2:
            # only cupy>=v2 supports cudnn7
            cudnns = [c for c in cudnns if c < 'cudnn7']
        if with_dummy:
            cudnns += ['cudnn-latest-with-dummy']

        for cudnn in cudnns:
            for nccl in nccls:
                choices.append((cuda, cudnn, nccl))

    if target == 'chainer':
        choices = [('none', 'none', 'none')] + choices

    return choices


def get_numpy_choices():
    choices = ['1.9', '1.10', '1.11', '1.12']
    cupy_version = version.get_cupy_version()
    if cupy_version is not None:
        if cupy_version[0] >= 2:
            # cupy v2 or later
            choices.append('1.13')
        if cupy_version[0:2] >= (4, 1):
            # cupy v4.1 or later
            choices.append('1.14')
    return choices


codes = {}

# base

codes['centos7_py27'] = '''FROM centos:7

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install gcc gcc-c++ git kmod hdf5-devel perl make autoconf xz && \\
    yum -y install python-devel python-pip && \\
    yum clean all
'''

codes['centos7_py34-pyenv'] = '''FROM centos:7

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install gcc gcc-c++ git kmod hdf5-devel perl make autoconf xz && \\
    yum -y install bzip2-devel openssl-devel readline-devel && \\
    yum clean all

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" pyenv install 3.4.8
RUN pyenv global 3.4.8
RUN pyenv rehash
'''

codes['centos6_py27-pyenv'] = '''FROM centos:6

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install gcc gcc-c++ git kmod hdf5-devel patch perl make autoconf && \\
    yum -y install bzip2-devel openssl-devel readline-devel && \\
    yum clean all

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" pyenv install 2.7.14
RUN pyenv global 2.7.14
RUN pyenv rehash
'''

codes['ubuntu14_py27'] = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ gfortran git libhdf5-dev autoconf xz-utils && \\
    apt-get -y install python-pip python-dev && \\
    apt-get -y install libffi-dev libssl-dev && \\
    apt-get clean
'''

codes['ubuntu14_py34'] = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ gfortran git libhdf5-dev autoconf xz-utils && \\
    apt-get -y install python3-pip python3-dev && \\
    apt-get clean

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
'''

ubuntu14_pyenv_base = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ gfortran git libhdf5-dev autoconf xz-utils && \\
    apt-get -y install libbz2-dev libreadline-dev libssl-dev make && \\
    apt-get clean

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" pyenv install {python_ver}
RUN pyenv global {python_ver}
RUN pyenv rehash
'''

codes['ubuntu14_py35-pyenv'] = ubuntu14_pyenv_base.format(python_ver='.'.join(
    [str(x) for x in get_python_version('ubuntu14_py35-pyenv')]))
codes['ubuntu14_py36-pyenv'] = ubuntu14_pyenv_base.format(python_ver='.'.join(
    [str(x) for x in get_python_version('ubuntu14_py36-pyenv')]))

codes['ubuntu16_py27'] = '''FROM ubuntu:16.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ g++-4.8 gfortran git autoconf libhdf5-dev libhdf5-serial-dev pkg-config && \\
    apt-get -y install python-pip python-dev && \\
    apt-get clean

RUN ln -s /usr/bin/gcc-4.8 /usr/local/bin/gcc
RUN ln -s /usr/bin/g++-4.8 /usr/local/bin/g++
'''

codes['ubuntu16_py35'] = '''FROM ubuntu:16.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ g++-4.8 gfortran git libhdf5-dev libhdf5-serial-dev pkg-config autoconf && \\
    apt-get -y install python3-pip python3-dev && \\
    apt-get clean

RUN ln -s /usr/bin/gcc-4.8 /usr/local/bin/gcc
RUN ln -s /usr/bin/g++-4.8 /usr/local/bin/g++

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
'''

# ccache

ccache = '''WORKDIR /opt/ccache
RUN curl -L -s -o ccache.tar.gz https://github.com/ccache/ccache/archive/v3.4.2.tar.gz && \\
    tar -xzf ccache.tar.gz && cd ccache-3.4.2 && \\
    ./autogen.sh && ./configure && make && \\
    cp ccache /usr/bin/ccache && \\
    cd / && rm -rf /opt/ccache && \\
    { cd /usr/lib64 || cd /usr/lib ; } && \\
    mkdir ccache && cd ccache && \\
    ln -s /usr/bin/ccache gcc && \\
    ln -s /usr/bin/ccache g++ && \\
    ln -s /usr/bin/ccache x86_64-linux-gnu-gcc && \\
    ln -s /usr/bin/ccache x86_64-linux-gnu-g++ && \\
    ln -s /usr/bin/ccache x86_64-redhat-linux-gcc && \\
    ln -s /usr/bin/ccache x86_64-redhat-linux-g++
ENV NVCC="ccache nvcc"
'''

# cuda

cuda70_run = 'cuda_7.0.28_linux.run'
cuda70_url = 'http://developer.download.nvidia.com/compute/cuda/7_0/Prod/local_installers'
cuda70_installer = 'cuda-linux64-rel-7.0.28-19326674.run'

cuda75_run = 'cuda_7.5.18_linux.run'
cuda75_url = 'http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers'
cuda75_driver = 'NVIDIA-Linux-x86_64-352.39.run'
cuda75_installer = 'cuda-linux64-rel-7.5.18-19867135.run'

cuda80_run = 'cuda_8.0.44_linux-run'
cuda80_url = 'https://developer.nvidia.com/compute/cuda/8.0/prod/local_installers'
cuda80_driver = 'NVIDIA-Linux-x86_64-367.48.run'
cuda80_installer = 'cuda-linux64-rel-8.0.44-21122537.run'

cuda90_run = 'cuda_9.0.176_384.81_linux-run'
cuda90_url = 'https://developer.nvidia.com/compute/cuda/9.0/Prod/local_installers'
cuda90_driver = 'NVIDIA-Linux-x86_64-384.81.run'
cuda90_installer = 'cuda-linux.9.0.176-22781540.run'

cuda91_run = 'cuda_9.1.85_387.26_linux'
cuda91_url = 'https://developer.nvidia.com/compute/cuda/9.1/Prod/local_installers'
cuda91_driver = 'NVIDIA-Linux-x86_64-387.26.run'
cuda91_installer = 'cuda-linux.9.1.85-23083092.run'

cuda92_run = 'cuda_9.2.88_396.26_linux'
cuda92_url = 'https://developer.nvidia.com/compute/cuda/9.2/Prod/local_installers'
cuda92_driver = 'NVIDIA-Linux-x86_64-396.26.run'
cuda92_installer = 'cuda-linux.9.2.88-23920284.run'


cuda_base = '''
WORKDIR /opt/nvidia
RUN mkdir installers && \\
    curl -sL -o {cuda_run} {cuda_url}/{cuda_run} && \\
    echo "{sha256sum}  {cuda_run}" | sha256sum -cw --quiet - && \\
    chmod +x {cuda_run} && sync && \\
    ./{cuda_run} -extract=`pwd`/installers && \\
    ./installers/{installer} -noprompt && \\
    cd / && \\
    rm -rf /opt/nvidia

RUN echo "/usr/local/cuda/lib" >> /etc/ld.so.conf.d/cuda.conf && \\
    echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && \\
    ldconfig

ENV CUDA_PATH /usr/local/cuda
ENV PATH $PATH:$CUDA_PATH/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_PATH/lib64:$CUDA_PATH/lib:/usr/local/nvidia/lib64:/usr/local/nvidia/lib
ENV LIBRARY_PATH /usr/local/nvidia/lib64:/usr/local/nvidia/lib:/usr/local/cuda/lib64/stubs$LIBRARY_PATH

ENV CUDA_VERSION {cuda_ver}
LABEL com.nvidia.volumes.needed="nvidia_driver"
LABEL com.nvidia.cuda.version="{cuda_ver}"
'''

codes['cuda70'] = cuda_base.format(
    cuda_ver='7.0',
    cuda_run=cuda70_run,
    cuda_url=cuda70_url,
    installer=cuda70_installer,
    sha256sum='d1292e9c2bbaddad24c46e0b0d15a7130831bfac0382f7159321f41ae385a5ce',
)

codes['cuda75'] = cuda_base.format(
    cuda_ver='7.5',
    cuda_run=cuda75_run,
    cuda_url=cuda75_url,
    installer=cuda75_installer,
    sha256sum='08411d536741075131a1858a68615b8b73c51988e616e83b835e4632eea75eec',
)

codes['cuda80'] = cuda_base.format(
    cuda_ver='8.0',
    cuda_run=cuda80_run,
    cuda_url=cuda80_url,
    installer=cuda80_installer,
    sha256sum='64dc4ab867261a0d690735c46d7cc9fc60d989da0d69dc04d1714e409cacbdf0',
)

codes['cuda90'] = cuda_base.format(
    cuda_ver='9.0',
    cuda_run=cuda90_run,
    cuda_url=cuda90_url,
    installer=cuda90_installer,
    sha256sum='96863423feaa50b5c1c5e1b9ec537ef7ba77576a3986652351ae43e66bcd080c',
)

codes['cuda91'] = cuda_base.format(
    cuda_ver='9.1',
    cuda_run=cuda91_run,
    cuda_url=cuda91_url,
    installer=cuda91_installer,
    sha256sum='8496c72b16fee61889f9281449b5d633d0b358b46579175c275d85c9205fe953',
)

codes['cuda92'] = cuda_base.format(
    cuda_ver='9.2',
    cuda_run=cuda92_run,
    cuda_url=cuda92_url,
    installer=cuda92_installer,
    sha256sum='8d02cc2a82f35b456d447df463148ac4cc823891be8820948109ad6186f2667c',
)

# cudnn

cudnn_base = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz && \\
    echo "{sha256sum}  {cudnn}.tgz" | sha256sum -cw --quiet - && \\
    tar -xzf {cudnn}.tgz -C /usr/local && \\
    rm {cudnn}.tgz

ENV CUDNN_VER {cudnn_ver}
'''

codes['cudnn4'] = cudnn_base.format(
    cudnn='cudnn-7.0-linux-x64-v4.0-prod',
    cudnn_ver='v4',
    sha256sum='cd091763d5889f0efff1fbda83bade191f530743a212c6b0ecc2a64d64d94405',
)

codes['cudnn5'] = cudnn_base.format(
    cudnn='cudnn-7.5-linux-x64-v5.0-ga',
    cudnn_ver='v5',
    sha256sum='c4739a00608c3b66a004a74fc8e721848f9112c5cb15f730c1be4964b3a23b3a',
)

codes['cudnn5-cuda8'] = cudnn_base.format(
    cudnn='cudnn-8.0-linux-x64-v5.0-ga',
    cudnn_ver='v5',
    sha256sum='af80eb1ce0cb51e6a734b2bdc599e6d50b676eab3921e5bddfe5443485df86b6',
)

codes['cudnn51'] = cudnn_base.format(
    cudnn='cudnn-7.5-linux-x64-v5.1',
    cudnn_ver='v5.1',
    sha256sum='69ca71f7728b54b6e003393083f419b24774fecd3b08bbf41bceac9a9fe16345',
)

codes['cudnn51-cuda8'] = cudnn_base.format(
    cudnn='cudnn-8.0-linux-x64-v5.1',
    cudnn_ver='v5.1',
    sha256sum='c10719b36f2dd6e9ddc63e3189affaa1a94d7d027e63b71c3f64d449ab0645ce',
)

codes['cudnn6'] = cudnn_base.format(
    cudnn='cudnn-7.5-linux-x64-v6.0',
    cudnn_ver='v6.0',
    sha256sum='568d4b070c5f91ab8a15b287b73dd072b99c7267a43edad13f70337cd186c82c',
)

codes['cudnn6-cuda8'] = cudnn_base.format(
    cudnn='cudnn-8.0-linux-x64-v6.0',
    cudnn_ver='v6.0',
    sha256sum='9b09110af48c9a4d7b6344eb4b3e344daa84987ed6177d5c44319732f3bb7f9c',
)

codes['cudnn7-cuda8'] = cudnn_base.format(
    cudnn='cudnn-8.0-linux-x64-v7',
    cudnn_ver='v7.0.5',
    sha256sum='9e0b31735918fe33a79c4b3e612143d33f48f61c095a3b993023cdab46f6d66e',
)

codes['cudnn7-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7',
    cudnn_ver='v7.0.5',
    sha256sum='1a3e076447d5b9860c73d9bebe7087ffcb7b0c8814fd1e506096435a2ad9ab0e',
)

codes['cudnn7-cuda91'] = cudnn_base.format(
    cudnn='cudnn-9.1-linux-x64-v7',
    cudnn_ver='v7.0.5',
    sha256sum='1ead5da7324db35dcdb3721a8d4fc020b217c68cdb3b3daa1be81eb2456bd5e5',
)

codes['cudnn71-cuda8'] = cudnn_base.format(
    cudnn='cudnn-8.0-linux-x64-v7.1',
    cudnn_ver='v7.1.3',
    sha256sum='31ed3c3bfb9c515c228c1dcbb306277ce08836e84e3facedef6182d872f8cd3d',
)

codes['cudnn71-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.1',
    cudnn_ver='v7.1.4',
    sha256sum='60b581d0f05324c33323024a264aa3fb185c533e2f67dae7fda847b926bb7e57',
)

codes['cudnn71-cuda91'] = cudnn_base.format(
    cudnn='cudnn-9.1-linux-x64-v7.1',
    cudnn_ver='v7.1.3',
    sha256sum='dd616d3794167ceb923d706bf73e8d6acdda770751492b921ee6827cdf190228',
)

codes['cudnn71-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.1',
    cudnn_ver='v7.1.4',
    sha256sum='f875340f812b942408098e4c9807cb4f8bdaea0db7c48613acece10c7c827101',
)

# This is a test for CFLAGS and LDFLAGS to specify a directory where cuDNN is
# installed.
codes['cudnn-latest-with-dummy'] = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz && \\
    echo "{sha256sum}  {cudnn}.tgz" | sha256sum -cw --quiet - && \\
    tar -xzf {cudnn}.tgz -C /opt/cudnn && \\
    rm {cudnn}.tgz
RUN mkdir -p /usr/local/cuda/include && \\
    mkdir -p /usr/local/cuda/lib64
RUN touch /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn.so
ENV CFLAGS=-I/opt/cudnn/cuda/include
ENV LDFLAGS=-L/opt/cudnn/cuda/lib64
ENV LD_LIBRARY_PATH=/opt/cudnn/cuda/lib64:$LD_LIBRARY_PATH
'''.format(
    cudnn='cudnn-8.0-linux-x64-v6.0',
    cudnn_ver='v6.0',
    sha256sum='9b09110af48c9a4d7b6344eb4b3e344daa84987ed6177d5c44319732f3bb7f9c',
)

# NCCL

codes['nccl1.3'] = '''
WORKDIR /opt/nccl
RUN curl -sL -o nccl1.3.4.tar.gz https://github.com/NVIDIA/nccl/archive/v1.3.4-1.tar.gz && \\
    tar zxf nccl1.3.4.tar.gz && \\
    cd nccl-1.3.4-1 && \\
    NVCC_GENCODE= make -j4 && \\
    make install
'''

nccl_base = '''
RUN mkdir nccl && cd nccl && \\
    curl -sL -o {libnccl2}.deb http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64/{libnccl2}.deb && \\
    curl -sL -o {libnccl_dev}.deb http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1604/x86_64/{libnccl_dev}.deb && \\
    ar vx {libnccl2}.deb && \\
    tar xvf data.tar.xz && \\
    ar vx {libnccl_dev}.deb && \\
    tar xvf data.tar.xz && \\
    cp .{include_dir}/* /usr/local/cuda/include && \\
    cp .{lib_dir}/* /usr/local/cuda/lib64 && \\
    cd .. && rm -rf nccl
'''

codes['nccl2.0-cuda8'] = nccl_base.format(
    libnccl2='libnccl2_2.0.5-2+cuda8.0_amd64',
    libnccl_dev='libnccl-dev_2.0.5-2+cuda8.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.0-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.0.5-3+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.0.5-3+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.2-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.2.12-1+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.2.12-1+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.1-cuda91'] = nccl_base.format(
    libnccl2='libnccl2_2.1.15-1+cuda9.1_amd64',
    libnccl_dev='libnccl-dev_2.1.15-1+cuda9.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.2-cuda92'] = nccl_base.format(
    libnccl2='libnccl2_2.2.12-1+cuda9.2_amd64',
    libnccl_dev='libnccl-dev_2.2.12-1+cuda9.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)


protobuf_cpp_base = '''
RUN echo /usr/local/lib >> /etc/ld.so.conf
RUN tmpdir=`mktemp -d` && \\
    cd $tmpdir && \\
    curl -sL -o protobuf-cpp-{protobuf}.tar.gz https://github.com/google/protobuf/releases/download/v{protobuf}/protobuf-cpp-{protobuf}.tar.gz && \\
    tar -xzf protobuf-cpp-{protobuf}.tar.gz && \\
    curl -sL -o protobuf-python-{protobuf}.tar.gz https://github.com/google/protobuf/releases/download/v{protobuf}/protobuf-python-{protobuf}.tar.gz && \\
    tar -xzf protobuf-python-{protobuf}.tar.gz && \\
    cd protobuf-{protobuf} && CC=/usr/bin/gcc CXX=/usr/bin/g++ ./configure && make -j4 install && ldconfig && \\
    cd python && python setup.py install --cpp_implementation && \\
    cd /tmp && rm -rf $tmpdir
WORKDIR /tmp
'''

codes['protobuf-cpp-3'] = protobuf_cpp_base.format(
    protobuf='3.3.0',
)

codes['none'] = ''


def set_env(env, value):
    return 'ENV {}={}\n'.format(env, value)


def partition_requirements(package, requires):
    target = None
    others = []

    for req in requires:
        if package in req:
            target = req
        else:
            others.append(req)
    return target, others


def make_dockerfile(conf):
    dockerfile = ''
    dockerfile += codes[conf['base']]
    if 'http_proxy' in conf:
        dockerfile += set_env('http_proxy', conf['http_proxy'])
    if 'https_proxy' in conf:
        dockerfile += set_env('https_proxy', conf['https_proxy'])
    dockerfile += codes[conf['cuda']]
    dockerfile += codes[conf['cudnn']]
    dockerfile += ccache
    dockerfile += codes[conf['nccl']]

    if 'protobuf-cpp' in conf:
        dockerfile += codes[conf['protobuf-cpp']]

    # Update old packages provided by OS.
    dockerfile += '''
RUN pip install -U pip six setuptools && rm -rf ~/.cache/pip
'''

    if 'ubuntu' in conf['base']:
        # The system's six is too old so that we have to use a newer one.
        # However, just running `pip install -U six` does not resolve the
        # situation; this command installs an upgraded six to /usr/local/lib,
        # while the old one is left at /usr/lib. Which one is used depends on
        # the user's environment which cannot be controlled. Therefore, we
        # remove the system's six after upgrading it.
        # HOWEVER, this removal then causes uninstallation of the system's pip!
        # It is because the system's pip depends on the system's six, and the
        # dependency is managed by apt, not pip. Therefore, we also have to
        # install a pip to /usr/local/lib using `pip install -U pip` before
        # removing it (via removing the system's six).
        dockerfile += '''\
RUN apt-get remove -y \\
        python3-pip python-pip python-pip-whl \\
        python3-six python-six python-six-whl \\
        python3-setuptools python-setuptools python-setuptools-whl \\
        python-pkg-resources python3-pkg-resources \\
        python3-chardet python-chardet python-chardet-whl
'''

    if 'requires' in conf:
        requires = conf['requires']
        if any(['theano' in req or 'scipy' in req for req in requires]):
            if 'ubuntu' in conf['base']:
                dockerfile += 'RUN apt-get update && apt-get -y install liblapack-dev && apt-get clean\n'
            elif 'centos' in conf['base']:
                dockerfile += 'RUN yum -y update && yum -y install lapack-devel && yum clean all\n'

        pillow, requires = partition_requirements('pillow', requires)
        scipy, requires = partition_requirements('scipy', requires)

        if pillow is not None:
            dockerfile += ('RUN pip install -U olefile && '
                           'pip install --global-option="build_ext" '
                           '--global-option="--disable-jpeg" -U "%s" && rm -rf ~/.cache/pip\n' % pillow)

        if 0 < len(requires):
            dockerfile += (
                'RUN pip install -U %s && rm -rf ~/.cache/pip\n' %
                ' '.join(['"%s"' % req for req in requires]))

        if scipy is not None:
            # SciPy depends on C-API interface of NumPy.
            # When you install different version of NumPy, it breaks compatibility and causes an error.
            # So you need to install SciPy from its source to link NumPy you use.
            dockerfile += 'RUN pip install --no-binary scipy -U "%s" && rm -rf ~/.cache/pip\n' % scipy

    # Make a user and home directory to install chainer
    dockerfile += 'RUN useradd -m -u %d user\n' % os.getuid()
    return dockerfile


def write_dockerfile(conf):
    dockerfile = make_dockerfile(conf)
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)


def build_image(name, no_cache=False):
    cmd = ['docker', 'build', '-t', name]
    if not sys.stdout.isatty():
        cmd.append('-q')
    if no_cache:
        cmd.append('--no-cache')
    cmd.append('.')

    subprocess.check_call(cmd)


def make_random_name():
    random.seed()
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for i in range(10))


def get_num_gpus():
    out = subprocess.check_output('nvidia-smi -L | wc -l', shell=True)
    return int(out)


def select_gpu(offset):
    num_gpus = get_num_gpus()
    gpus = list(range(num_gpus))
    offset %= len(gpus)
    gpus = gpus[offset:] + gpus[:offset]
    return gpus


def run_with(conf, script, no_cache=False, volume=None, env=None,
             timeout=None, gpu_id=None, use_root=False):
    write_dockerfile(conf)
    name = make_random_name()

    build_image(name, no_cache)

    # run
    host_cwd = os.getcwd()
    work_dir = '/work'
    run_name = make_random_name()
    signal.signal(signal.SIGTERM, make_handler(run_name))
    signal.signal(signal.SIGINT, make_handler(run_name))
    cmd = ['nvidia-docker', 'run',
           '--rm',
           '--name=%s' % run_name,
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir]
    if not use_root:
        cmd += ['-u', str(os.getuid())]

    if gpu_id is not None:
        gpus = select_gpu(gpu_id)
        cmd += ['-e', 'CUDA_VISIBLE_DEVICES=' + ','.join(map(str, gpus))]

    if volume:
        for v in volume:
            cmd += ['-v', '%s:%s' % (v, v)]
    if env:
        for var, val in env.items():
            cmd += ['-e', '%s=%s' % (var, val)]

    cmd.append(name)
    if timeout:
        cmd += ['timeout', str(timeout)]
    cmd.append(script)

    res = subprocess.call(cmd)
    if res != 0:
        logging.error('Failed to run test')
        logging.error('Exit code: %d' % res)
        exit(1)


def run_interactive(
        conf, no_cache=False, volume=None, env=None, use_root=False):
    name = make_random_name()

    write_dockerfile(conf)
    build_image(name, no_cache)

    host_cwd = os.getcwd()
    work_dir = '/work'
    cmd = ['nvidia-docker', 'run',
           '--rm',
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir,
           '-i', '-t']
    if not use_root:
        cmd += ['-u', str(os.getuid())]
    if volume:
        for v in volume:
            cmd += ['-v', '%s:%s' % (v, v)]
    if env:
        for var, val in env.items():
            cmd += ['-e', '%s=%s' % (var, val)]

    cmd += [name, '/bin/bash']

    subprocess.call(cmd)


def make_handler(name):
    def kill(signum, frame):
        print('Stopping docker...')
        cmd = ['docker', 'kill', name]
        try:
            subprocess.check_call(cmd)
        except Exception as e:
            logging.error('Failed to kill docker process')
            logging.error(str(e))
            sys.exit(-1)

    return kill
