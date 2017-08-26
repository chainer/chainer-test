#!/bin/sh -ex

cd cupy
python setup.py -q sdist --cupy-no-cuda
tar -l dist/*.tar.gz | grep .cpp
