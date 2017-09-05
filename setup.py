#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    # TODO: put package requirements here
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='pyrosbag',
    version='0.1.3',
    description="Programmatically control ROS Bag files with Python",
    long_description=readme + '\n\n' + history,
    author="Jean Nassar",
    author_email='jeannassar5@gmail.com',
    url='https://github.com/masasin/pyrosbag',
    packages=[
        'pyrosbag',
    ],
    package_dir={'pyrosbag':
                 'pyrosbag'},
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords=['pyrosbag', 'ros', 'bag'],
    download_url = "https://github.com/masasin/pyrosbag/tarball/0.1.0",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
