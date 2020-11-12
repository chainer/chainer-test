import logging
import os
import random
import signal
import string
import subprocess
import sys

import version


_base_choices = [
    ('ubuntu16_py35', '3.5.2'),
    ('ubuntu16_py36-pyenv', '3.6.6'),
    ('ubuntu16_py37-pyenv', '3.7.0'),
    ('ubuntu18_py36', '3.6.7'),
    ('ubuntu18_py37-pyenv', '3.7.1'),
    ('ubuntu18_py38-pyenv', '3.8.0'),
    ('centos7_py34-pyenv', '3.4.8')]

base_choices_all = [a[0] for a in _base_choices]

# Python 3.5+
base_choices_master = [
    a[0] for a in _base_choices if
    (a[1].startswith('3.') and not a[1].startswith('3.4.'))]

# Python 2.7 & 3.5+
base_choices_stable_chainer = [
    a[0] for a in _base_choices if
    a[1].startswith('2.') or
    (a[1].startswith('3.') and not a[1].startswith('3.4.'))]

# Python 2.7 & 3.4+
base_choices_stable_cupy = base_choices_all

cuda_choices = [
    'none',
    'cuda90', 'cuda92',
    'cuda100', 'cuda101', 'cuda102',
    'cuda110', 'cuda111',
]
cudnn_choices = [
    'none',
    'cudnn7-cuda9',
    'cudnn71-cuda9', 'cudnn71-cuda92',
    'cudnn72-cuda9', 'cudnn72-cuda92',
    'cudnn73-cuda9', 'cudnn73-cuda92', 'cudnn73-cuda100',
    'cudnn74-cuda9', 'cudnn74-cuda92', 'cudnn74-cuda100',
    'cudnn75-cuda9', 'cudnn75-cuda92', 'cudnn75-cuda100', 'cudnn75-cuda101',
    'cudnn76-cuda102',
    'cudnn80-cuda110', 'cudnn80-cuda111',
]
nccl_choices = [
    'none',
    'nccl2.0-cuda9',
    'nccl2.2-cuda9', 'nccl2.2-cuda92',
    'nccl2.3-cuda9', 'nccl2.3-cuda92', 'nccl2.3-cuda100',
    'nccl2.4-cuda9', 'nccl2.4-cuda92', 'nccl2.4-cuda100', 'nccl2.4-cuda101',
    'nccl2.5-cuda9', 'nccl2.5-cuda100', 'nccl2.5-cuda101', 'nccl2.5-cuda102',
    'nccl2.6-cuda100', 'nccl2.6-cuda101', 'nccl2.6-cuda102',
    'nccl2.7-cuda101', 'nccl2.7-cuda102', 'nccl2.7-cuda110', 'nccl2.7-cuda111'
]
cutensor_choices = [
    'none',
    'cutensor1.2.0-cuda101',
    'cutensor1.2.0-cuda102',
    'cutensor1.2.0-cuda110',
    'cutensor1.2.0-cuda111',
]

cuda_cudnns = {
    'cuda90': ['cudnn7-cuda9', 'cudnn71-cuda9', 'cudnn72-cuda9',
               'cudnn73-cuda9', 'cudnn74-cuda9', 'cudnn75-cuda9'],
    'cuda92': ['cudnn71-cuda92', 'cudnn72-cuda92', 'cudnn73-cuda92',
               'cudnn74-cuda92', 'cudnn75-cuda92'],
    'cuda100': ['cudnn73-cuda100', 'cudnn74-cuda100', 'cudnn75-cuda100'],
    'cuda101': ['cudnn75-cuda101'],
    'cuda102': ['cudnn76-cuda102'],
    'cuda110': ['cudnn80-cuda110'],
    'cuda111': ['cudnn80-cuda111'],
}
cuda_nccls = {
    # CUDA 9 does not support nccl 1.3
    'cuda90': ['nccl2.0-cuda9', 'nccl2.2-cuda9', 'nccl2.3-cuda9',
               'nccl2.4-cuda9', 'nccl2.5-cuda9'],
    'cuda92': ['nccl2.2-cuda92', 'nccl2.3-cuda9', 'nccl2.4-cuda92'],
    'cuda100': ['nccl2.3-cuda100', 'nccl2.4-cuda100', 'nccl2.5-cuda100',
                'nccl2.6-cuda100'],
    'cuda101': ['nccl2.4-cuda101', 'nccl2.5-cuda101', 'nccl2.6-cuda101',
                'nccl2.7-cuda101'],
    'cuda102': ['nccl2.5-cuda102', 'nccl2.6-cuda102', 'nccl2.7-cuda102'],
    'cuda110': ['nccl2.7-cuda110'],
    'cuda111': ['nccl2.7-cuda111'],
}
cuda_cutensors = {
    'cuda101': ['cutensor1.2.0-cuda101'],
    'cuda102': ['cutensor1.2.0-cuda102'],
    'cuda110': ['cutensor1.2.0-cuda110'],
    'cuda111': ['cutensor1.2.0-cuda111'],
}


def get_python_version(base):
    """Returns the python version to be installed in a tuple."""
    ver = next(a[1] for a in _base_choices if a[0] == base)
    return tuple([int(s) for s in ver.split('.')])


def get_cuda_libs_choices(target, with_dummy=False):
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
        cutensors = ['none'] + cuda_cutensors.get(cuda, [])
        if cupy_major < 2:
            # only cupy>=v2 supports cudnn7
            cudnns = [c for c in cudnns if c < 'cudnn7']
        if with_dummy:
            cudnns += ['cudnn-latest-with-dummy']

        for cudnn in cudnns:
            for nccl in nccls:
                for cutensor in cutensors:
                    choices.append((cuda, cudnn, nccl, cutensor))

    if target == 'chainer':
        choices = [('none', 'none', 'none', 'none')] + choices

    return choices


def get_numpy_choices():
    cupy_version = version.get_cupy_version()
    if cupy_version[0] < 8:
        choices = [
            '1.9', '1.10', '1.11', '1.12', '1.13', '1.14', '1.15', '1.16',
            '1.17']
    else:
        # cupy v8 or later
        choices = ['1.16', '1.17', '1.18', '1.19']
    return choices


codes = {}

# base

codes['centos7_py34-pyenv'] = '''FROM centos:7

ENV PATH /usr/lib64/ccache:$PATH

# devtoolset-6 needs to be activated by: `source /opt/rh/devtoolset-6/enable`
RUN yum -y update && \\
    yum -y install centos-release-scl epel-release && \\
    yum -y install devtoolset-6 gcc gcc-c++ git kmod hdf5-devel which perl make autoconf xz && \\
    yum -y install bzip2-devel openssl-devel readline-devel && \\
    yum clean all

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install 3.4.8
RUN pyenv global 3.4.8
RUN pyenv rehash

ENV CUTENSOR_URL=https://developer.download.nvidia.com/compute/cuda/repos/rhel7/x86_64/

ENV CUTENSOR_INSTALL='install_cutensor() {{ curl -sL -o libcutensor1_$1-1_amd64.rpm $CUTENSOR_URL/libcutensor1-$1-1.x86_64.rpm && \\
    rpm -i libcutensor1_$1-1_amd64.rpm && \\
    rm libcutensor1_$1-1_amd64.rpm && \\
    curl -sL -o libcutensor-dev_$1-1_amd64.rpm $CUTENSOR_URL/libcutensor-devel-$1-1.x86_64.rpm && \\
    rpm -i libcutensor-dev_$1-1_amd64.rpm  && \\
    rm libcutensor-dev_$1-1_amd64.rpm && \\
    update-alternatives --set libcutensor.so.$2 /usr/lib64/libcutensor/$3/libcutensor.so.$2 ; \\
    }}';
'''

cutensor_ubuntu_install = '''
ENV CUTENSOR_URL=https://developer.download.nvidia.com/compute/cuda/repos/ubuntu{cutensor_os_ver}/x86_64

ENV CUTENSOR_INSTALL='install_cutensor() {{ curl -sL -o libcutensor1_$1-1_amd64.deb $CUTENSOR_URL/libcutensor1_$1-1_amd64.deb && \\
    dpkg -i libcutensor1_$1-1_amd64.deb && \\
    rm libcutensor1_$1-1_amd64.deb && \\
    curl -sL -o libcutensor-dev_$1-1_amd64.deb $CUTENSOR_URL/libcutensor-dev_$1-1_amd64.deb && \\
    dpkg -i libcutensor-dev_$1-1_amd64.deb  && \\
    rm libcutensor-dev_$1-1_amd64.deb && \\
    update-alternatives --set libcutensor.so.$2 /usr/lib/x86_64-linux-gnu/libcutensor/$3/libcutensor.so.$2 ; \\
    }};'
'''

ubuntu16_apt_install_gcc = '''
RUN apt-get -y update && \
    apt-get -y install software-properties-common && \\
    add-apt-repository ppa:ubuntu-toolchain-r/test && \\
    apt-get -y update && \\
    apt-get -y install g++-6 && \\
    apt-get clean
'''

ubuntu_pyenv_base = '''FROM ubuntu:{ubuntu_ver}

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ gfortran git libhdf5-dev autoconf xz-utils pkg-config && \\
    apt-get -y install libbz2-dev libreadline-dev libffi-dev libssl-dev make cmake && \\
    apt-get clean

{gcc_install}

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install {python_ver}
RUN pyenv global {python_ver}
RUN pyenv rehash

{cutensor_ubuntu_install}
'''

codes['ubuntu16_py36-pyenv'] = ubuntu_pyenv_base.format(
    ubuntu_ver='16.04',
    python_ver='.'.join(
        [str(x) for x in get_python_version('ubuntu16_py36-pyenv')]),
    gcc_install=ubuntu16_apt_install_gcc,
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1604')
)
codes['ubuntu16_py37-pyenv'] = ubuntu_pyenv_base.format(
    ubuntu_ver='16.04',
    python_ver='.'.join(
        [str(x) for x in get_python_version('ubuntu16_py37-pyenv')]),
    gcc_install=ubuntu16_apt_install_gcc,
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1604')
)
codes['ubuntu18_py37-pyenv'] = ubuntu_pyenv_base.format(
    ubuntu_ver='18.04',
    python_ver='.'.join(
        [str(x) for x in get_python_version('ubuntu18_py37-pyenv')]),
    gcc_install='',
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1804')
)
codes['ubuntu18_py38-pyenv'] = ubuntu_pyenv_base.format(
    ubuntu_ver='18.04',
    python_ver='.'.join(
        [str(x) for x in get_python_version('ubuntu18_py38-pyenv')]),
    gcc_install='',
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1804')
)

codes['ubuntu16_py35'] = '''FROM ubuntu:16.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ cmake gfortran git libhdf5-dev libhdf5-serial-dev pkg-config autoconf && \\
    apt-get -y install python3-pip python3-dev && \\
    apt-get clean

{gcc_install}

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

{cutensor_ubuntu_install}
'''.format(
    gcc_install=ubuntu16_apt_install_gcc,
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1604'))

codes['ubuntu18_py36'] = '''FROM ubuntu:18.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && \\
    apt-get -y upgrade && \\
    apt-get -y install curl g++ cmake gfortran git libhdf5-dev libhdf5-serial-dev pkg-config autoconf && \\
    apt-get -y install python3-pip python3-dev && \\
    apt-get clean

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

{cutensor_ubuntu_install}
'''.format(
    cutensor_ubuntu_install=cutensor_ubuntu_install.format(
        cutensor_os_ver='1604'))

# ccache

ccache = '''WORKDIR /opt/ccache
RUN curl -L -s -o ccache.tar.gz https://github.com/ccache/ccache/archive/v3.5.tar.gz && \\
    tar -xzf ccache.tar.gz && cd ccache-3.5 && \\
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

cuda90_run = 'cuda_9.0.176_384.81_linux-run'
cuda90_url = 'https://developer.nvidia.com/compute/cuda/9.0/Prod/local_installers'

cuda92_run = 'cuda_9.2.88_396.26_linux'
cuda92_url = 'https://developer.nvidia.com/compute/cuda/9.2/Prod/local_installers'

cuda100_run = 'cuda_10.0.130_410.48_linux'
cuda100_url = 'https://developer.nvidia.com/compute/cuda/10.0/Prod/local_installers'

cuda101_run = 'cuda_10.1.243_418.87.00_linux.run'
cuda101_url = 'https://developer.download.nvidia.com/compute/cuda/10.1/Prod/local_installers'

cuda102_run = 'cuda_10.2.89_440.33.01_linux.run'
cuda102_url = 'https://developer.download.nvidia.com/compute/cuda/10.2/Prod/local_installers'

cuda110_run = 'cuda_11.0.2_450.51.05_linux.run'
cuda110_url = 'https://developer.download.nvidia.com/compute/cuda/11.0.2/local_installers'

cuda111_run = 'cuda_11.1.0_455.23.05_linux.run'
cuda111_url = 'https://developer.download.nvidia.com/compute/cuda/11.1.0/local_installers'


cuda_base = '''
WORKDIR /opt/nvidia
RUN curl -sL -o {cuda_run} {cuda_url}/{cuda_run} && \\
    echo "{sha256sum}  {cuda_run}" | sha256sum -cw --quiet - && \\
    chmod +x {cuda_run} && sync && \\
    ./{cuda_run} --silent --toolkit && \\
    ls -al /usr/local/cuda && \\
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

codes['cuda90'] = cuda_base.format(
    cuda_ver='9.0',
    cuda_run=cuda90_run,
    cuda_url=cuda90_url,
    sha256sum='96863423feaa50b5c1c5e1b9ec537ef7ba77576a3986652351ae43e66bcd080c',
)

codes['cuda92'] = cuda_base.format(
    cuda_ver='9.2',
    cuda_run=cuda92_run,
    cuda_url=cuda92_url,
    sha256sum='8d02cc2a82f35b456d447df463148ac4cc823891be8820948109ad6186f2667c',
)

codes['cuda100'] = cuda_base.format(
    cuda_ver='10.0',
    cuda_run=cuda100_run,
    cuda_url=cuda100_url,
    sha256sum='92351f0e4346694d0fcb4ea1539856c9eb82060c25654463bfd8574ec35ee39a',
)

codes['cuda101'] = cuda_base.format(
    cuda_ver='10.1',
    cuda_run=cuda101_run,
    cuda_url=cuda101_url,
    sha256sum='e7c22dc21278eb1b82f34a60ad7640b41ad3943d929bebda3008b72536855d31',
)

codes['cuda102'] = cuda_base.format(
    cuda_ver='10.2',
    cuda_run=cuda102_run,
    cuda_url=cuda102_url,
    sha256sum='560d07fdcf4a46717f2242948cd4f92c5f9b6fc7eae10dd996614da913d5ca11',
)

codes['cuda110'] = cuda_base.format(
    cuda_ver='11.0',
    cuda_run=cuda110_run,
    cuda_url=cuda110_url,
    sha256sum='48247ada0e3f106051029ae8f70fbd0c238040f58b0880e55026374a959a69c1',
)

codes['cuda111'] = cuda_base.format(
    cuda_ver='11.1',
    cuda_run=cuda111_run,
    cuda_url=cuda111_url,
    sha256sum='858cbab091fde94556a249b9580fadff55a46eafbcb4d4a741d2dcd358ab94a5',
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

codes['cudnn7-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7',
    cudnn_ver='v7.0.5',
    sha256sum='1a3e076447d5b9860c73d9bebe7087ffcb7b0c8814fd1e506096435a2ad9ab0e',
)

codes['cudnn71-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.1',
    cudnn_ver='v7.1.4',
    sha256sum='60b581d0f05324c33323024a264aa3fb185c533e2f67dae7fda847b926bb7e57',
)

codes['cudnn71-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.1',
    cudnn_ver='v7.1.4',
    sha256sum='f875340f812b942408098e4c9807cb4f8bdaea0db7c48613acece10c7c827101',
)

codes['cudnn72-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.2.1.38',
    cudnn_ver='v7.2.1',
    sha256sum='cf007437b9ac6250ec63b89c25f248d2597fdd01369c80146567f78e75ce4e37',
)

codes['cudnn72-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.2.1.38',
    cudnn_ver='v7.2.1',
    sha256sum='3e78f5f0edbe614b56f00ff2d859c5409d150c87ae6ba3df09f97d537909c2e9',
)

codes['cudnn73-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.3.1.20',
    cudnn_ver='v7.3.1',
    sha256sum='fc7980cd3663a7e6e8f043b9a07a2631940fbd030e1faf9027404474bdc5b196',
)

codes['cudnn73-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.3.1.20',
    cudnn_ver='v7.3.1',
    sha256sum='aa652e95e66deb2970247fdeb5c5f6ae8b30ab6a35050df1354613acb1da6d05',
)

codes['cudnn73-cuda100'] = cudnn_base.format(
    cudnn='cudnn-10.0-linux-x64-v7.3.1.20',
    cudnn_ver='v7.3.1',
    sha256sum='4e15a323f2edffa928b4574f696fc0e449a32e6bc35c9ccb03a47af26c2de3fa',
)

codes['cudnn74-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.4.1.5',
    cudnn_ver='v7.4.1',
    sha256sum='bec38fc281fec0226766cce050473043765345cb8a5ed699da4d663ecfa4f24d',
)

codes['cudnn74-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.4.1.5',
    cudnn_ver='v7.4.1',
    sha256sum='a850d62f32c6a18271932d9a96072ac757c2c516bd1200ae8b79e4bdd3800b5b',
)

codes['cudnn74-cuda100'] = cudnn_base.format(
    cudnn='cudnn-10.0-linux-x64-v7.4.1.5',
    cudnn_ver='v7.4.1',
    sha256sum='b320606f1840eec0cdd4453cb333554a3fe496dd4785f10d8e87fe1a4f52bd5c',
)

codes['cudnn75-cuda9'] = cudnn_base.format(
    cudnn='cudnn-9.0-linux-x64-v7.5.0.56',
    cudnn_ver='v7.5.0',
    sha256sum='ee0ecd3cc30b9bf5ec875eac3ed375d3996bcb0ed5d2551716e4884b3ea5ce8c',
)

codes['cudnn75-cuda92'] = cudnn_base.format(
    cudnn='cudnn-9.2-linux-x64-v7.5.0.56',
    cudnn_ver='v7.5.0',
    sha256sum='2a04fd5ed5b8d32e2401c85a1a38f3cfd6da662c31bd26e80bea25469e48a675',
)

codes['cudnn75-cuda100'] = cudnn_base.format(
    cudnn='cudnn-10.0-linux-x64-v7.5.0.56',
    cudnn_ver='v7.5.0',
    sha256sum='701097882cb745d4683bb7ff6c33b8a35c7c81be31bac78f05bad130e7e0b781',
)

codes['cudnn75-cuda101'] = cudnn_base.format(
    cudnn='cudnn-10.1-linux-x64-v7.5.0.56',
    cudnn_ver='v7.5.0',
    sha256sum='c31697d6b71afe62838ad2e57da3c3c9419c4e9f5635d14b683ebe63f904fbc8',
)

codes['cudnn76-cuda102'] = cudnn_base.format(
    cudnn='cudnn-10.2-linux-x64-v7.6.5.32',
    cudnn_ver='v7.6.5',
    sha256sum='600267f2caaed2fd58eb214ba669d8ea35f396a7d19b94822e6b36f9f7088c20',
)

codes['cudnn80-cuda110'] = cudnn_base.format(
    cudnn='cudnn-11.0-linux-x64-v8.0.2.39',
    cudnn_ver='v8.0.2',
    sha256sum='672f46288b8edd98f8d156a4f1ff518201ca6de0cff67915ceaa37f6d6d86345',
)
codes['cudnn80-cuda111'] = cudnn_base.format(
    cudnn='cudnn-11.1-linux-x64-v8.0.4.30',
    cudnn_ver='v8.0.4',
    sha256sum='8f4c662343afce5998ce963500fe3bb167e9a508c1a1a949d821a4b80fa9beab',
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

codes['nccl2.0-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.0.5-3+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.0.5-3+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.2-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.2.13-1+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.2.13-1+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.2-cuda92'] = nccl_base.format(
    libnccl2='libnccl2_2.2.13-1+cuda9.2_amd64',
    libnccl_dev='libnccl-dev_2.2.13-1+cuda9.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.3-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.3.7-1+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.3.7-1+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.3-cuda92'] = nccl_base.format(
    libnccl2='libnccl2_2.3.7-1+cuda9.2_amd64',
    libnccl_dev='libnccl-dev_2.3.7-1+cuda9.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.3-cuda100'] = nccl_base.format(
    libnccl2='libnccl2_2.3.7-1+cuda10.0_amd64',
    libnccl_dev='libnccl-dev_2.3.7-1+cuda10.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.4-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.4.2-1+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.4.2-1+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.4-cuda92'] = nccl_base.format(
    libnccl2='libnccl2_2.4.2-1+cuda9.2_amd64',
    libnccl_dev='libnccl-dev_2.4.2-1+cuda9.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.4-cuda100'] = nccl_base.format(
    libnccl2='libnccl2_2.4.2-1+cuda10.0_amd64',
    libnccl_dev='libnccl-dev_2.4.2-1+cuda10.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.4-cuda101'] = nccl_base.format(
    libnccl2='libnccl2_2.4.2-1+cuda10.1_amd64',
    libnccl_dev='libnccl-dev_2.4.2-1+cuda10.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.5-cuda9'] = nccl_base.format(
    libnccl2='libnccl2_2.5.6-1+cuda9.0_amd64',
    libnccl_dev='libnccl-dev_2.5.6-1+cuda9.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.5-cuda100'] = nccl_base.format(
    libnccl2='libnccl2_2.5.6-1+cuda10.0_amd64',
    libnccl_dev='libnccl-dev_2.5.6-1+cuda10.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.5-cuda101'] = nccl_base.format(
    libnccl2='libnccl2_2.5.6-1+cuda10.1_amd64',
    libnccl_dev='libnccl-dev_2.5.6-1+cuda10.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.5-cuda102'] = nccl_base.format(
    libnccl2='libnccl2_2.5.6-1+cuda10.2_amd64',
    libnccl_dev='libnccl-dev_2.5.6-1+cuda10.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.6-cuda100'] = nccl_base.format(
    libnccl2='libnccl2_2.6.4-1+cuda10.0_amd64',
    libnccl_dev='libnccl-dev_2.6.4-1+cuda10.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.6-cuda101'] = nccl_base.format(
    libnccl2='libnccl2_2.6.4-1+cuda10.1_amd64',
    libnccl_dev='libnccl-dev_2.6.4-1+cuda10.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.6-cuda102'] = nccl_base.format(
    libnccl2='libnccl2_2.6.4-1+cuda10.2_amd64',
    libnccl_dev='libnccl-dev_2.6.4-1+cuda10.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.7-cuda101'] = nccl_base.format(
    libnccl2='libnccl2_2.7.3-1+cuda10.1_amd64',
    libnccl_dev='libnccl-dev_2.7.3-1+cuda10.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.7-cuda102'] = nccl_base.format(
    libnccl2='libnccl2_2.7.3-1+cuda10.2_amd64',
    libnccl_dev='libnccl-dev_2.7.3-1+cuda10.2_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)

codes['nccl2.7-cuda110'] = nccl_base.format(
    libnccl2='libnccl2_2.7.3-1+cuda11.0_amd64',
    libnccl_dev='libnccl-dev_2.7.3-1+cuda11.0_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)
codes['nccl2.7-cuda111'] = nccl_base.format(
    libnccl2='libnccl2_2.7.8-1+cuda11.1_amd64',
    libnccl_dev='libnccl-dev_2.7.8-1+cuda11.1_amd64',
    include_dir='/usr/include',
    lib_dir='/usr/lib/x86_64-linux-gnu',
)


# cuTENSOR
# The shell script needs to be saved in an env var due to Dockerfile limitations
codes['cutensor1.2.0-cuda101'] = 'RUN eval $CUTENSOR_INSTALL && install_cutensor 1.2.0.2 1.2.0 10.1;'
codes['cutensor1.2.0-cuda102'] = 'RUN eval $CUTENSOR_INSTALL && install_cutensor 1.2.0.2 1.2.0 10.2;'
codes['cutensor1.2.0-cuda110'] = 'RUN eval $CUTENSOR_INSTALL && install_cutensor 1.2.0.2 1.2.0 11.0;'
codes['cutensor1.2.0-cuda111'] = 'RUN eval $CUTENSOR_INSTALL && install_cutensor 1.2.0.2 1.2.0 11.1;'

protobuf_cpp_base = '''
RUN echo /usr/local/lib >> /etc/ld.so.conf
RUN tmpdir=`mktemp -d` && \\
    cd $tmpdir && \\
    curl -sL -o protobuf-cpp-{protobuf}.tar.gz https://github.com/google/protobuf/releases/download/v{protobuf}/protobuf-cpp-{protobuf}.tar.gz && \\
    tar -xzf protobuf-cpp-{protobuf}.tar.gz && \\
    curl -sL -o protobuf-python-{protobuf}.tar.gz https://github.com/google/protobuf/releases/download/v{protobuf}/protobuf-python-{protobuf}.tar.gz && \\
    tar -xzf protobuf-python-{protobuf}.tar.gz && \\
    cd protobuf-{protobuf} && CC=/usr/bin/gcc CXX=/usr/bin/g++ ./configure && make -j4 install && ldconfig && \\
    cd python && CC=/usr/bin/gcc CXX=/usr/bin/g++ python setup.py install --cpp_implementation && \\
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
    dockerfile += codes[conf['cutensor']]

    if 'protobuf-cpp' in conf:
        dockerfile += codes[conf['protobuf-cpp']]

    # Update old packages provided by OS.
    dockerfile += '''
RUN pip install -U pip six 'setuptools<50' && rm -rf ~/.cache/pip
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

        if pillow is not None:
            dockerfile += ('RUN pip install olefile && '
                           'pip install --global-option="build_ext" '
                           '--global-option="--disable-jpeg" -U "%s" && rm -rf ~/.cache/pip\n' % pillow)

        if 0 < len(requires):
            dockerfile += (
                'RUN pip install %s && rm -rf ~/.cache/pip\n' %
                ' '.join(['"%s"' % req for req in requires]))

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
