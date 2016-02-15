import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test script for multi-environment')
    parser.add_argument('--test', choices=[
        'ubuntu14_py2', 'ubuntu14_py3', 'py35', 'example', 'prev_example', 'doc'
    ])
    parser.add_argument('--http-proxy')
    parser.add_argument('--https-proxy')
    parser.add_argument('-i', 'interactive', action='store_true')
    args = parser.parse_args()

    conf = {
        'base': 'ubuntu14_py2',
        'cuda': 'cuda70',
        'cudnn': 'cudnn3',
    }

    dockr.run_with(conf, './test_install.sh')
