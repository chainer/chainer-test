from allpairspy import AllPairs


_test_axes = [
    ('base',    ['ubuntu14', 'ubuntu16', 'centos6', 'centos7']),
    ('python',  ['2.7', '3.4', '3.5', '3.6']),
    ('numpy',   ['1.9', '1.10', '1.11', '1.12', '1.13', '1.14']),
    ('scipy',   [None, '0.19']),
    ('ideep',   [None, '1.0.3']),
    ('cuda',    ['7', '7.5', '8.0', '9.0', '9.1']),
    ('cudnn',   [None, '4', '5', '5.1', '6', '7']),
    ('nccl',    [None, '1', '2']),
]

test_param_keys = [x[0] for x in _test_axes]
test_param_values = [x[1] for x in _test_axes]


def _validate_numpy(numpy, python):
    valid = []
    if numpy == '1.9':
        valid = ['2.7', '3.4']
    elif numpy == '1.10':
        valid = ['2.7', '3.4']
    elif numpy == '1.11':
        valid = ['2.7', '3.4', '3.5']
    elif numpy == '1.12':
        valid = ['2.7', '3.4', '3.5', '3.6']
    elif numpy == '1.13':
        valid = ['2.7', '3.4', '3.5', '3.6']
    elif numpy == '1.14':
        valid = ['2.7', '3.4', '3.5', '3.6']
    return python in valid


def _validate_ideep(ideep, python, numpy):
    if ideep is None:
        return True

    valid_pythons = ['2.7', '3.5', '3.6']
    valid_numpys = ['1.13', '1.14']
    return python in valid_pythons and numpy in valid_numpys


def _validate_cuda_cudnn_nccl(cuda, cudnn, nccl):
    valid_cudnns = [None]
    valid_nccls = [None]

    if cuda == '7':
        valid_cudnns = ['4']
    elif cuda == '7.5':
        valid_cudnns = ['4', '5', '5.1', '6', '7']
        valid_nccls = ['1']
    elif cuda == '8.0':
        valid_cudnns = ['5', '5.1', '6', '7']
        valid_nccls = ['1', '2']
    elif cuda == '9.0':
        valid_cudnns = ['7']
        valid_nccls = ['1', '2']
    elif cuda == '9.1':
        valid_cudnns = ['7']
        valid_nccls = ['1', '2']
    return cudnn in valid_cudnns and nccl in valid_nccls


def _validate_param(param, func, *keys):
    args = ()
    for key in keys:
        if not key in param:
            return True
        args += param[key],
    return func(*args)


def is_valid_combination(row):
    p = dict(zip(test_param_keys, row))
    return all([
        _validate_param(p, _validate_numpy, 'numpy', 'python'),
        _validate_param(p, _validate_ideep, 'ideep', 'python', 'numpy'),
        _validate_param(p, _validate_cuda_cudnn_nccl, 'cuda', 'cudnn', 'nccl'),
    ])


def generate_test_cases():
    for i, pairs in enumerate(AllPairs(test_param_values, filter_func=is_valid_combination)):
        print("{:2d}: {}".format(
            i,
            ',  '.join(['{} = {}'.format(k ,v) for (k, v) in zip(test_param_keys, pairs)])))

if __name__ == '__main__':
    generate_test_cases()
