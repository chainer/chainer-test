#!/usr/bin/env python

import argparse
import sys

import docker


def _generate_matrix(libname, matrix):
    """Generate Groovy expression of all acceptable version combinations.

    This can be used for Jenkins configuration.
    """
    conditions = []
    for cuda in sorted(matrix.keys()):
        versions = sorted(set(
            [fq_libver.split('-')[0] for fq_libver in matrix[cuda]]))
        conditions += [
            '(CUDA == \'{}\' && {} in {})'.format(cuda, libname, versions)
        ]

    return ' || '.join(conditions)


def generate_cudnn_matrix():
    return _generate_matrix('CUDNN', docker.cuda_cudnns)


def generate_nccl_matrix():
    return _generate_matrix('NCCL', docker.cuda_nccls)


def _get_fully_qualified_version_id(cuda, libver, matrix):
    if cuda == 'none':
        if libver != 'none':
            raise RuntimeError('library version must be none if cuda is none')
        return libver
    elif cuda not in matrix.keys():
        raise RuntimeError(
            'unsupported cuda version: '
            'must be any of: {}'.format(matrix.keys()))

    for fq_libver in sorted(matrix[cuda]):
        if libver == fq_libver or fq_libver.startswith('{}-'.format(libver)):
            return fq_libver

    raise RuntimeError('unsupported library version: {}'.format(libver))


def get_cudnn_id(cuda, cudnn):
    """Translate cuDNN version (without CUDA version suffix) into
    fully-qualified version identifier.

    e.g., ('cuda70', 'cudnn6') -> 'cudnn6'
          ('cuda80', 'cudnn6') -> 'cudnn6-cuda8'
    """
    return _get_fully_qualified_version_id(cuda, cudnn, docker.cuda_cudnns)


def get_nccl_id(cuda, nccl):
    """Translate NCCL version (without CUDA version suffix) into
    fully-qualified version identifier.

    e.g., ('cuda70', 'nccl1.3.4') -> 'nccl1.3.4'
          ('cuda80', 'nccl2.0')   -> 'nccl2.0-cuda8'
    """
    return _get_fully_qualified_version_id(cuda, nccl, docker.cuda_nccls)


def main(args):
    parser = argparse.ArgumentParser(
        description='CUDA Matrix Test Generator')
    parser.add_argument('--generate-cudnn-matrix', action='store_true')
    parser.add_argument('--generate-nccl-matrix', action='store_true')
    parser.add_argument('--get-cudnn-id', action='store_true')
    parser.add_argument('--get-nccl-id', action='store_true')

    # For --get-{cudnn,nccl}-id:
    parser.add_argument('--cuda', default='none')
    parser.add_argument('--cudnn', default='none')
    parser.add_argument('--nccl', default='none')

    params = parser.parse_args(args)

    if params.get_cudnn_id:
        print(get_cudnn_id(params.cuda, params.cudnn))
    elif params.get_nccl_id:
        print(get_nccl_id(params.cuda, params.nccl))
    elif params.generate_cudnn_matrix:
        print(generate_cudnn_matrix())
    elif params.generate_nccl_matrix:
        print(generate_nccl_matrix())
    else:
        parser.error('no action specified')


if __name__ == '__main__':
    main(sys.argv[1:])
