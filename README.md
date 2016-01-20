# chainer-test

It is test scripts of chainer and dockerfiles for its test environment.


## Requiements

- Docker (>=1.6)
- CUDA 7.5

## Prepararaiton

Prepare these files to ```/opt/cuda```

- ```cuda_6.5.19_linux_64.run```
- ```cuda_7.0.28_linux.run```
- ```cuda_7.5.18_linux.run```
- ```cudnn-6.5-linux-x64-v2.tgz```
- ```cudnn-7.0-linux-x64-v3.0-prod.tgz```
- ```cudnn-7.0-linux-x64-v4.0-rc.tgz```

## How to use

First run `prepare.py` to copy files which are required to make a Docker image.
And then, run `make_docker.py` to make a `Dockerfile` for an environemnt you want to test.

```
$ ./prepare.py --cuda=cuda70 --cudnn=cudnn2
$ ./make_docker.py --base=ubuntu14_py2 --numpy=numpy19 --cuda=cuda70 --cudnn=cudnn2
$ docker build -t chainer_test .
$ docker run --env COVERALLS_REPO_TOKEN=XXX..X -v ${pwd}:/work -w /work \
  --device /dev/nvidia0:/dev/nvidia0 \
  --device /dev/nvidiactl:/dev/nvidiactl \
  --device /dev/nvidia-uvm:/dev/nvidia-uvm ./test.sh
```

## Test scripts

- `test.sh`: build and run all tests.
- `test_cpu.sh`: build and run only tests for CPUs.
- `test_example.sh`: build and run all examples.
- `test_example.sh`: build and run all examples of previous version.
- `test_doc.sh`: build the document and run document test.
- `test_install.sh`: make source distribution package and install it with given environment.


## In Jenkins

Make a multi-configuration project.
In the matrix configuration, make four variables, `BASE`, `CUDA`, `CUDNN` and `NUMPY`.
You can make a configuration matrix for all combination.
