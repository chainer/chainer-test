FROM ubuntu:14.04

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get install -y curl g++ gfortran python-pip python-dev

RUN pip install numpy

WORKDIR /opt/nvidia
ENV CUDA_RUN cuda_6.5.19_linux_64.run
ENV CUDA_URL http://developer.download.nvidia.com/compute/cuda/6_5/rel/installers/$CUDA_RUN
RUN curl -silent -o $CUDA_RUN $CUDA_URL && \
    chmod +x $CUDA_RUN && \
    mkdir installers && \
    ./$CUDA_RUN -extract=`pwd`/installers && \
    cd installers && \
    ./NVIDIA-Linux-x86_64-343.19.run -s -N --no-kernel-module && \
    ./cuda-linux64-rel-6.5.19-18849900.run -noprompt && \
    cd / && \
    rm -rf /opt/nvidia

ENV CUDA_ROOT /usr/local/cuda-6.5
ENV PATH $PATH:$CUDA_ROOT/bin
ENV LD_LIBRARY_PATH $LD_LIBRARY_PATH:$CUDA_ROOT/lib64:$CUDA_ROOT/lib
