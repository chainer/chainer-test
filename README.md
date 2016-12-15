# chainer-test

It is test scripts of chainer and dockerfiles for its test environment.


## Requiements

- CuPy (when GPU mode)
- nvidia-docker
- Docker (>=1.7)
- CUDA 8.0

## How to use

Run test scripts with options that specify the environment to test.

```
$ ./run_multi_test.py --base=ubuntu14_py2 --numpy=1.9 --cuda=cuda70 --cudnn=cudnn2 --type=gpu
```

These test scripts create `Dockerfile`, make containers, and run appropriate test scripts.


## Scripts to run

- `run_install_test.py`: Installation test.
- `run_test.py`: Build and run test scripts. It includes unit tests with commonly-used environment settings, tests for examples and ones for documents
- `run_multi_test.py`: Build and run test scripts. It can test all combinations of environment setting.


## In Jenkins

Make a multi-configuration project.
In the matrix configuration, make four variables, `BASE`, `CUDA`, `CUDNN` and `NUMPY`.
You can make a configuration matrix for all combination.
