# chainer-test

It is test scripts of chainer and dockerfiles for its test environment.


## Requirements

- CuPy (when GPU mode)
- nvidia-docker
- Docker (>=1.7)
- CUDA 8.0

## How to use

Run test scripts with options that specify the environment to test.

```
$ ./run_multi_test.py --base=ubuntu16_py35 --numpy=1.9 --cuda=cuda80 --cudnn=cudnn5-cuda8 --type=gpu
```

These test scripts create `Dockerfile`, make containers, and run appropriate test scripts.


## Scripts to run

### Common

- `run_test.py`: Build and run test scripts. It includes unit tests with commonly-used environment settings, tests for examples and ones for documents.
    - Test Scripts:
        - `test.sh`: Chainer unittests
        - `test_example.sh`: Chainer examples
        - `test_prev_example.sh`: Chainer examples from previous version (to test API compatibility)
        - `test_doc.sh`: Chainer documents
        - `test_cupy.sh`: CuPy unittests
        - `test_cupy_example.sh`: CuPy examples
        - `test_cupy_doc.sh`: CuPy documents

### Chainer-specific

- `run_install_test.py`: Installation test.
    - Test Scripts:
        - `build_sdist.sh`: build sdist for Chainer
        - `test_install.sh`: install Chainer

- `run_multi_test.py`: Build and run test scripts. It can test all combinations of environment setting; convenient to run tests against specific environment manually.
    - Test Scripts:
        - `test.sh`: GPU mode
        - `test_cpu.sh`: CPU mode

- `run_combination_test.py`: Build and run test scripts. Environment combination (e.g., base operating system, CUDA/cuDNN version, etc.) are randomly determined by `--id`; mainly expected for use with CI.
    - Test Scripts:
        - `test.sh`: GPU mode
        - `test_cpu.sh`: CPU mode

- `run_docker_test.py`: Test Dockerfile of Chainer.
    - Test Scripts: none

### CuPy-specific

- `run_cupy_install_test.py`: CuPy equivalent of `run_install_test.py`
    - Test Scripts:
        - `build_sdist_cupy.sh`: build sdist for CuPy
        - `test_cupy_install.sh`: install CuPy

- `run_cupy_combination_test.py`: CuPy equivalent of `run_combination_test.py`
    - Test Scripts:
        - `test_cupy.sh`

## In Jenkins

Make a multi-configuration project.
In the matrix configuration, define variables (axis) that corresponds to the argument of scripts and kick the script (`run_*.py`) with the variable.
