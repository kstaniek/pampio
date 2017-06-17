#!/usr/bin/env python

import re
from setuptools import setup, find_packages


def version():
    pyfile = 'pampio/version.py'
    with open(pyfile) as fp:
        data = fp.read()

    match = re.search("__version__ = '([^']+)'", data)
    assert match, 'cannot find version in {}'.format(pyfile)
    return match.group(1)

setup(name='pampio',
      version=version(),
      description='A Python Ampio Server IP client implementation',
      url='http://github.com/kstaniek/pampio',
      author='Klaudiusz Staniek',
      author_email='kstaniek@gmail.com',
      license='Apache 2.0',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Topic :: System :: Hardware :: Hardware Drivers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5'
      ],
      packages=find_packages(),
      keywords='ampio automation',
      zip_safe=False)
