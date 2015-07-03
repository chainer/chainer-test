# chainer-test

It is test scripts of chainer and dockerfiles for its test environment.


## Requiements

- Docker (>=1.6)
- CUDA 6.5

## How to use

```
$ cp /path/to/cudnn-6.5-linux-x64-v2 .
$ docker build -f Dockerfile.ubuntu14_cuda_cudnn -t chainer_test .
$ docker run --env COVERALLS_REPO_TOKEN=XXX..X -v ${pwd}:/work -w /work \
  --device /dev/nvidia0:/dev/nvidia0 \
  --device /dev/nvidiactl:/dev/nvidiactl \
  --device /dev/nvidia-uvm:/dev/nvidia-uvm ./test.sh
```
