import logging
import os
import subprocess


base_choices = ['ubuntu14_py2', 'ubuntu14_py3', 'ubuntu14_py35', 'centos7_py2', 'centos7_py3']
cuda_choices = ['none', 'cuda65', 'cuda70', 'cuda75']
cudnn_choices = ['none', 'cudnn2', 'cudnn3', 'cudnn4-rc']


codes = {}

# base

codes['centos7_py2'] = '''FROM centos:7

RUN yum -y update
RUN yum -y install epel-release
RUN yum -y install ccache gcc gcc-c++ git kmod hdf5-devel perl

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y install python-devel python-pip
'''

codes['centos7_py3'] = '''FROM centos:7

RUN yum -y update
RUN yum -y install epel-release
RUN yum -y install ccache gcc gcc-c++ git kmod hdf5-devel perl

ENV PATH /usr/lib64/ccache:$PATH

RUN yum -y install bzip2-devel make openssl-devel readline-devel
RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install 3.4.3
RUN pyenv global 3.4.3
RUN pyenv rehash
'''

codes['ubuntu14_py2'] = '''FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y ccache curl g++ gfortran git libhdf5-dev

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get install -y python-pip python-dev
'''

codes['ubuntu14_py3'] = '''FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y ccache curl g++ gfortran git libhdf5-dev

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get install -y python3-pip python3-dev
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
'''

codes['ubuntu14_py35'] = '''FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y ccache curl g++ gfortran git libhdf5-dev

ENV PATH /usr/lib/ccache:$PATH

RUN apt-get -y install libbz2-dev libreadline-dev libssl-dev make
RUN git clone git://github.com/yyuu/pyenv.git /opt/pyenv
ENV PYENV_ROOT=/opt/pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

RUN pyenv install 3.5.0
RUN pyenv global 3.5.0
RUN pyenv rehash
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
RUN mkdir installers

RUN curl -s -o {cuda_run} {cuda_url}/{cuda_run}

RUN chmod +x {cuda_run} && sync && \\
    ./{cuda_run} -extract=`pwd`/installers
RUN ./installers/{installer} -noprompt && \\
    cd / && \\
    rm -rf /opt/nvidia

RUN echo "/usr/local/cuda/lib" >> /etc/ld.so.conf.d/cuda.conf && \
    echo "/usr/local/cuda/lib64" >> /etc/ld.so.conf.d/cuda.conf && \
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
)

codes['cuda70'] = cuda_base.format(
    cuda_ver='7.0',
    cuda_run=cuda70_run,
    cuda_url=cuda70_url,
    installer=cuda70_installer,
)

codes['cuda75'] = cuda_base.format(
    cuda_ver='7.5',
    cuda_run=cuda75_run,
    cuda_url=cuda75_url,
    installer=cuda75_installer,
)

# cudnn

cudnn2_base = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz
RUN tar -xzf {cudnn}.tgz
RUN rm {cudnn}.tgz
RUN cp {cudnn}/cudnn.h /usr/local/cuda/include/.
RUN mv {cudnn}/libcudnn.so /usr/local/cuda/lib64/.
RUN mv {cudnn}/libcudnn.so.6.5 /usr/local/cuda/lib64/.
RUN mv {cudnn}/libcudnn.so.6.5.48 /usr/local/cuda/lib64/.
RUN mv {cudnn}/libcudnn_static.a /usr/local/cuda/lib64/.
'''

codes['cudnn2'] = cudnn2_base.format(
    cudnn='cudnn-6.5-linux-x64-v2',
    cudnn_ver='v2',
)

cudnn_base = '''
WORKDIR /opt/cudnn
RUN curl -s -o {cudnn}.tgz http://developer.download.nvidia.com/compute/redist/cudnn/{cudnn_ver}/{cudnn}.tgz
RUN tar -xzf {cudnn}.tgz -C /usr/local
RUN rm {cudnn}.tgz
'''

codes['cudnn3'] = cudnn_base.format(
    cudnn='cudnn-7.0-linux-x64-v3.0-prod',
    cudnn_ver='v3',
)

codes['cudnn4-rc'] = cudnn_base.format(
    cudnn='cudnn-7.0-linux-x64-v4.0-rc',
    cudnn_ver='v4',
)

codes['none'] = ''


def set_env(env, value):
    return 'ENV {}={}\n'.format(env, value)


def run_pip(requires):
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

    if 'requires' in conf:
        for req in conf['requires']:
            dockerfile += run_pip(req)

    return dockerfile


def write_dockerfile(conf):
    dockerfile = make_dockerfile(conf)
    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)


def build_image(name, no_cache=False):
    cmd = ['docker', 'build', '-t', name, '.']
    if no_cache:
        cmd.append('--no-cache')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    subprocess.call(['grep', '-v', 'Sending build context'], stdin=p.stdout)
    res = p.wait()
    if res != 0:
        logging.error('Failed to create an image')
        logging.error('Exit code: %d' % res)
        exit(res)


def run_with(conf, script, no_cache=False, volume=None, env=None):
    write_dockerfile(conf)
    name = 'test'

    build_image(name, no_cache)

    # run
    failed = False
    host_cwd = os.getcwd()
    work_dir = '/work'
    cmd = ['nvidia-docker', 'run',
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir]

    if volume:
        for v in volume:
            cmd += ['-v', '%s:%s' % (v, v)]
    if env:
        for var, val in env.items():
            cmd += ['-e', '%s=%s' % (var, val)]

    cmd += [name, script]

    res = subprocess.call(cmd)
    if res != 0:
        logging.error('Failed to run test')
        logging.error('Exit code: %d' % res)
        failed = True

    # chown for clean up
    res = subprocess.call([
        'docker', 'run',
        '--rm',
        '-v', '%s:%s' % (host_cwd, work_dir),
        '-w', work_dir,
        name,
        '/bin/bash', '-c',
        'chown `stat -c %u .`:`stat -c %g .` -R .'])
    if res != 0:
        logging.error('Failed to chown')
        logging.error('Exit code: %d' % res)
        failed = True

    if failed:
        exit(1)


def run_interactive(conf, no_cache=False, volume=None, env=None):
    name = 'test'

    write_dockerfile(conf)
    build_image(name, no_cache)

    host_cwd = os.getcwd()
    work_dir = '/work'
    cmd = ['nvidia-docker', 'run',
           '-rm',
           '-v', '%s:%s' % (host_cwd, work_dir),
           '-w', work_dir,
           '-i', '-t']
    if volume:
        for v in volume:
            cmd += ['-v', '%s:%s' % (v, v)]
    if env:
        for var, val in env.items():
            cmd += ['-e', '%s=%s' % (var, val)]

    cmd += [name, '/bin/bash']

    res = subprocess.call(cmd)
