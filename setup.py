import re

from setuptools import find_packages
from setuptools import setup

__author__ = 'Roland Hedberg'


def readme():
    with open("README.md") as f:
        return f.read()


_pkg_name = "idpyoidc_backend"

version = "0.0.1"

setup(
    name=_pkg_name,
    version=version,
    description="Identity python OIDC backend module for Satosa",
    long_description=readme(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    author="Roland Hedberg",
    author_email="roland@catalogix.se",
    license="Apache 2.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "satosa>=8.0.0",
        "openid4v",
        "idpyoidc>=4.0.0",
    ],
)
