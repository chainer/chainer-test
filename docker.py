import logging
import os
import random
import re
import shutil
import signal
import string
import subprocess
import sys


base_choices = [
    'ubuntu14_py2', 'ubuntu14_py3', 'ubuntu14_py35', 'ubuntu14_py36',
    'ubuntu16_py2', 'ubuntu16_py3',
    'centos6_py2', 'centos7_py2', 'centos7_py3']
cuda_choices = ['none', 'cuda65', 'cuda70', 'cuda75', 'cuda80']
cudnn_choices = [
    'none', 'cudnn2', 'cudnn3', 'cudnn4', 'cudnn5', 'cudnn5-cuda8', 'cudnn51',
    'cudnn51-cuda8']


codes = {}

# base

codes['centos7_py2'] = '''FROM centos:7

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install ccache gcc gcc-c++ git kmod hdf5-devel perl make && \\
    yum clean all
RUN yum -y install python-devel python-pip && \\
    yum clean all
'''

codes['centos7_py3'] = '''FROM centos:7

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install ccache gcc gcc-c++ git kmod hdf5-devel perl make && \\
    yum clean all
RUN yum -y install bzip2-devel openssl-devel readline-devel && \\
    yum clean all

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" pyenv install 3.4.5
RUN pyenv global 3.4.5
RUN pyenv rehash
'''

codes['centos6_py2'] = '''FROM centos:6

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y update && \\
    yum -y install epel-release && \\
    yum -y install ccache gcc gcc-c++ git kmod hdf5-devel patch perl make && \\
    yum -y install bzip2-devel openssl-devel readline-devel && \\
    yum clean all

RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
RUN mkdir "$PYENV_ROOT/shims"
RUN chmod o+w "$PYENV_ROOT/shims"
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN cd "$PYENV_ROOT" && git pull && cd - && env CFLAGS="-fPIC" pyenv install 2.7.13
RUN pyenv global 2.7.13
RUN pyenv rehash
'''

codes['ubuntu14_py2'] = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && apt-get -y upgrade && \\
    apt-get install -y ccache curl g++ gfortran git libhdf5-dev && \\
    apt-get clean
RUN apt-get install -y python-pip python-dev && \\
    apt-get clean
'''

codes['ubuntu14_py3'] = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && apt-get -y upgrade && \\
    apt-get install -y ccache curl g++ gfortran git libhdf5-dev && \\
    apt-get clean
RUN apt-get install -y python3-pip python3-dev && \\
    apt-get clean

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
'''

ubuntu14_pyenv_base = '''FROM ubuntu:14.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && apt-get -y upgrade && \\
    apt-get install -y ccache curl g++ gfortran git libhdf5-dev && \\
    apt-get clean
RUN apt-get -y install libbz2-dev libreadline-dev libssl-dev make && \\
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

codes['ubuntu14_py35'] = ubuntu14_pyenv_base.format(python_ver='3.5.3')
codes['ubuntu14_py36'] = ubuntu14_pyenv_base.format(python_ver='3.6.0')

codes['ubuntu16_py2'] = '''FROM ubuntu:16.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && apt-get -y upgrade && \\
    apt-get install -y ccache curl g++ g++-4.8 gfortran git libhdf5-dev libhdf5-serial-dev pkg-config && \\
    apt-get clean
RUN apt-get install -y python-pip python-dev && \\
    apt-get clean

RUN ln -s /usr/bin/gcc-4.8 /usr/local/bin/gcc
RUN ln -s /usr/bin/g++-4.8 /usr/local/bin/g++
'''

codes['ubuntu16_py3'] = '''FROM ubuntu:16.04

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y update && apt-get -y upgrade && \\
    apt-get install -y ccache curl g++ g++-4.8 gfortran git libhdf5-dev libhdf5-serial-dev pkg-config && \\
    apt-get clean
RUN apt-get install -y python3-pip python3-dev && \\
    apt-get clean

RUN ln -s /usr/bin/gcc-4.8 /usr/local/bin/gcc
RUN ln -s /usr/bin/g++-4.8 /usr/local/bin/g++

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
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

cuda80_run = 'cuda_8.0.44_linux-run'
cuda80_url = 'https://developer.nvidia.com/compute/cuda/8.0/prod/local_installers/'
cuda80_driver = 'NVIDIA-Linux-x86_64-367.48.run'
cuda80_installer = 'cuda-linux64-rel-8.0.44-21122537.run'

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

ENV CUDA_ROOT /usr/local/cuda
ENV PATH $PATH:$CUDA_ROOT/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_ROOT/lib64:$CUDA_ROOT/lib:/usr/local/nvidia/lib64:/usr/local/nvidia/lib
ENV LIBRARY_PATH /usr/local/nvidia/lib64:/usr/local/nvidia/lib:/usr/local/cuda/lib64/stubs$LIBRARY_PATH

ENV CUDA_VERSION {cuda_ver}
LABEL com.nvidia.volumes.needed="nvidia_driver"
LABEL com.nvidia.cuda.version="{cuda_ver}"
'''

codes['cuda65'] = cuda_base.format(
    cuda_ver='6.5',
    cuda_run=cuda65_run,
    cuda_url=cuda65_url,
    installer=cuda65_installer,
    sha256sum='5279bc159b72b7445d8aae5f289d24bb4042c35422ef32da68049d8f666d3ff5',
)

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

# cudnn

cudnn2_base = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz && \\
    echo "{sha256sum}  {cudnn}.tgz" | sha256sum -cw --quiet - && \\
    tar -xzf {cudnn}.tgz && \\
    rm {cudnn}.tgz && \\
    mkdir -p /usr/local/cuda/include && \\
    mkdir -p /usr/local/cuda/lib64 && \\
    mv {cudnn}/cudnn.h /usr/local/cuda/include/. && \\
    mv {cudnn}/libcudnn.so /usr/local/cuda/lib64/. && \\
    mv {cudnn}/libcudnn.so.6.5 /usr/local/cuda/lib64/. && \\
    mv {cudnn}/libcudnn.so.6.5.48 /usr/local/cuda/lib64/. && \\
    mv {cudnn}/libcudnn_static.a /usr/local/cuda/lib64/.

ENV CUDNN_VER {cudnn_ver}
'''

codes['cudnn2'] = cudnn2_base.format(
    cudnn='cudnn-6.5-linux-x64-v2',
    cudnn_ver='v2',
    sha256sum='4b02cb6bf9dfa57f63bfff33e532f53e2c5a12f9f1a1b46e980e626a55f380aa',
)

cudnn_base = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz && \\
    echo "{sha256sum}  {cudnn}.tgz" | sha256sum -cw --quiet - && \\
    tar -xzf {cudnn}.tgz -C /usr/local && \\
    rm {cudnn}.tgz

ENV CUDNN_VER {cudnn_ver}
'''

codes['cudnn3'] = cudnn_base.format(
    cudnn='cudnn-7.0-linux-x64-v3.0-prod',
    cudnn_ver='v3',
    sha256sum='98679d5ec039acfd4d81b8bfdc6a6352d6439e921523ff9909d364e706275c2b',
)

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

# This is a test for CFLAGS and LDFLAGS to specify a directory where cuDNN is
# installed.
codes['cudnn51-with-dummy'] = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz && \\
    echo "{sha256sum}  {cudnn}.tgz" | sha256sum -cw --quiet - && \\
    tar -xzf {cudnn}.tgz -C /opt/cudnn && \\
    rm {cudnn}.tgz
RUN touch /usr/local/cuda/include/cudnn.h /usr/local/cuda/lib64/libcudnn.so
ENV CFLAGS=-I/opt/cudnn/cuda/include
ENV LDFLAGS=-L/opt/cudnn/cuda/lib64
ENV LD_LIBRARY_PATH=/opt/cudnn/cuda/lib64:$LD_LIBRARY_PATH
'''.format(
    cudnn='cudnn-8.0-linux-x64-v5.1',
    cudnn_ver='v5.1',
    sha256sum='a87cb2df2e5e7cc0a05e266734e679ee1a2fadad6f06af82a76ed81a23b102c8',
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
    protobuf='3.1.0',
)

codes['none'] = ''


def set_env(env, value):
    return 'ENV {}={}\n'.format(env, value)


def run_pip(requires):
    if 'pillow' in requires:
        return ('RUN pip install -U olefile && '
                'pip install --global-option="build_ext" '
                '--global-option="--disable-jpeg" -U "%s"\n' % requires)
    else:
        return 'RUN pip install -U "%s"\n' % requires


def make_dockerfile(conf):
    dockerfile = ''
    dockerfile += codes[conf['base']]
    if 'http_proxy' in conf:
        dockerfile += set_env('http_proxy', conf['http_proxy'])
    if 'https_proxy' in conf:
        dockerfile += set_env('https_proxy', conf['https_proxy'])
    dockerfile += codes[conf['cuda']]
    dockerfile += codes[conf['cudnn']]

    if 'protobuf-cpp' in conf:
        dockerfile += codes[conf['protobuf-cpp']]

    if 'requires' in conf:
        for req in conf['requires']:
            if 'theano' in req:
                if 'ubuntu' in conf['base']:
                    dockerfile += 'RUN apt-get update && apt-get -y install liblapack-dev && apt-get clean\n'
                elif 'centos' in conf['base']:
                    dockerfile += 'RUN yum -y update && yum -y install lapack-devel && yum clean all\n'
            dockerfile += run_pip(req)

    # Make a user and home directory to install chainer
    dockerfile += 'RUN useradd -m -u %d user\n' % os.getuid()
    return dockerfile


def write_dockerfile(conf):
    dockerfile = make_dockerfile(conf)
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)


def build_image(name, no_cache=False):
    cmd = ['docker', 'build', '-t', name]
    if no_cache:
        cmd.append('--no-cache')
    cmd.append('.')

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    subprocess.call(['grep', '-v', 'Sending build context'], stdin=p.stdout)
    res = p.wait()
    if res != 0:
        logging.error('Failed to create an image')
        logging.error('Exit code: %d' % res)
        exit(res)


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
             timeout=None, gpu_id=None):
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
           '--name=%s' % run_name,
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir,
           '-u', str(os.getuid())]

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


def run_interactive(conf, no_cache=False, volume=None, env=None):
    name = make_random_name()

    write_dockerfile(conf)
    build_image(name, no_cache)

    host_cwd = os.getcwd()
    work_dir = '/work'
    cmd = ['nvidia-docker', 'run',
           '--rm',
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir,
           '-u', str(os.getuid()),
           '-i', '-t']
    if volume:
        for v in volume:
            cmd += ['-v', '%s:%s' % (v, v)]
    if env:
        for var, val in env.items():
            cmd += ['-e', '%s=%s' % (var, val)]

    cmd += [name, '/bin/bash']

    res = subprocess.call(cmd)


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
