FROM ubuntu:14.04

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y g++ python-pip wget python-dev

#RUN wget -q http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1404/x86_64/cuda-repo-ubuntu1404_7.0-28_amd64.deb
#RUN dpkg -i ./cuda-repo-ubuntu1404_7.0-28_amd64.deb
#RUN apt-get update -y
#RUN apt-get install -y cuda

#RUN wget -q http://developer.download.nvidia.com/compute/cuda/6_5/rel/installers/cuda_6.5.14_linux_64.run && chmod +x cuda_6.5.14_linux_64.run
#RUN wget -q http://developer.download.nvidia.com/compute/cuda/7_0/Prod/local_installers/cuda_7.0.28_linux.run && chmod +x cuda_7.0.28_linux.run
#RUN ./cuda_7.0.28_linux.run --silent --driver
#RUN ./cuda_7.0.28_linux.run --silent --toolkit

WORKDIR /opt/nvidia
ENV CUDA_RUN cuda_6.5.19_linux_64.run
ENV CUDA_URL http://developer.download.nvidia.com/compute/cuda/6_5/rel/installers/$CUDA_RUN
RUN wget -q $CUDA_URL && \
    chmod +x $CUDA_RUN && \
    mkdir installers && \
    ./$CUDA_RUN -extract=`pwd`/installers && \
    cd installers && \
    ./NVIDIA-Linux-x86_64-343.19.run -s -N --no-kernel-module && \
    ./cuda-linux64-rel-6.5.19-18849900.run -noprompt && \
    cd / && \
    rm -rf /opt/nvidia

RUN pip install --upgrade six

ENV CUDA_ROOT /usr/local/cuda-6.5
ENV PATH $PATH:$CUDA_ROOT/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_ROOT/lib64:$CUDA_ROOT/lib
CMD cd chainer && pip install -e .

