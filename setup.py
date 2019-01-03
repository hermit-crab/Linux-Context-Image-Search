#!/bin/python
from setuptools import setup, find_packages


setup(
    name='searchbyimage',
    version='0.0.2',
    packages=find_packages(),
    install_requires=[
        'pycurl',
        'python3-xlib',
        'python3-keybinder',
        'psutil'
    ],
    package_data={
        '': ['res/*'],
    },
    entry_points={
        'console_scripts': [
            'searchbyimage = searchbyimage.__main__:main',
        ]
    },
)
