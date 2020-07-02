#!/bin/sh

if [ -f /opt/rh/devtoolset-6/enable ]; then
    source /opt/rh/devtoolset-6/enable
fi

export NVCC="${NVCC} --compiler-bindir gcc-6"
