#!/bin/sh

if [ "${CUPY_V8}" != 0 ]; then
    if [ -f /opt/rh/devtoolset-6/enable ]; then
        source /opt/rh/devtoolset-6/enable
    fi
    export NVCC="${NVCC} --compiler-bindir gcc-6"
fi
