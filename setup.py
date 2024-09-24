# CLAGE modbus python module
#
# python setup.py sdist bdist_wheel
# twine upload dist/*
#
# see https://www.seanh.cc/2022/05/21/publishing-python-packages-from-github-actions/
#   https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/
#   https://pythonprogramming.org/automatically-building-python-package-using-github-actions/

from setuptools import setup, find_packages

setup(
    name='calge_modbus',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'crcmod==1.7',
        'minimalmodbus==2.1.1',
        'pymodbus==2.1.0',
        'pyserial==3.5',
        'pyserial_asyncio==0.6',
        'python_dateutil==2.8.1'
    ],
)

#EOF
