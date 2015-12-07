import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'django-multiurl',
    version = '1.1.0',
    description = 'Allow multiple views to match the same URL.',
    license = 'BSD',
    long_description = read('README.rst'),
    url = 'https://github.com/raiderrober/django-multiurl',

    author = 'Jacob Kaplan-Moss and Robert Roskam',
    author_email = 'raiderrobert@gmail.com',

    py_modules = ['multiurl'],
    install_requires = ['django>=1.5'],

    classifiers = (
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
    ),
)
