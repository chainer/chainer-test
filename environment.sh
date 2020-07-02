#!/bin/sh

if [ -f /opt/rh/devtoolset-7/enable ]; then
    source /opt/rh/devtoolset-7/enable
fi

export NVCC="${NVCC} --compiler-bindir gcc-7"
