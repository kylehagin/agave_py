from setuptools import setup, Extension

fast_utils = Extension('validator_py.fast_utils', ['fast_utils.c'])

setup(
    name='validator_py',
    version='0.1',
    packages=['validator_py'],
    ext_modules=[fast_utils],
)
