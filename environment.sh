#!/bin/sh

# CuPy v8 requires g++-6 or later to build CUB.
if [ "${CUPY_V8}" != 0 ]; then
    if [ -f /opt/rh/devtoolset-6/enable ]; then
        # For CentOS 7, load environment variables for devtoolset-6.
        . /opt/rh/devtoolset-6/enable
    fi

    if which g++-6; then
        # For Ubuntu 16.04 and CentOS 7, use g++-6.
        # For Ubuntu 18.04, uses the default g++-7.
        export NVCC="${NVCC} --compiler-bindir gcc-6"
    fi
fi
