# TODO(niboshi): This module is only temporary workarounds for ideep tests.
# When they're fixed in ideep, avoid using these features and eventually
# remove this module.


# TODO(niboshi): Avoid using this when ideep is released on PyPI
def get_package_spec(version):
    # version is ignored
    return 'git+https://github.com/intel/ideep@hotfix_v1_0_0a#egg=ideep4py&subdirectory=python'


# TODO(niboshi): Avoid using this when NumPy is no longer imported from ideep's setup.py.
def pop_ideep_requirement(requires):
    # If `requires` includes ideep, pops it and returns it (`requires` is modified in-place).
    # Otherwise `None` will be returned.

    for req in requires:
        if 'ideep' in req:
            requires.remove(req)
            return req

    return None
