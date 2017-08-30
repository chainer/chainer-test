#!/bin/sh -ex

cd cupy
python setup.py -q sdist --cupy-no-cuda
tar -t -f dist/*.tar.gz | grep .cpp
