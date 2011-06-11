#!/usr/bin/env python
from setuptools import setup, find_packages
import os

parent_directory = os.path.abspath(os.path.dirname(__file__))

meta_files = {
    'README.md': None,
    'CLASSIFIERS.txt': None,
}

for filename in meta_files:
    try:
        current_file = open(os.path.join(parent_directory, filename))
        meta_files[filename] = current_file.read()
        current_file.close()
    except IOError:
        raise IOError('{0} not found.'.format(filename))

setup(name='django-webbugger',
      version='0.1',
      description='Basic webbugger/tracking beacon for django',
      long_description=meta_files['README.md'],
      classifiers=meta_files['CLASSIFIERS.txt'],
      author='Brandon R. Stoner',
      author_email='monokrome@limpidtech.com',
      url='http://limpidtech.com',
      packages=find_packages(),
      keywords = 'web django tracking',
      include_package_data = True,
      zip_safe = False,
)

