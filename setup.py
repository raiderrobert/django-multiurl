from setuptools import setup, find_packages

setup(
    name='django-multiurl',
    py_modules=['multiurl'],
    version='1.1.0',
    description='Allow multiple views to match the same URL.',
    license='BSD',
    url='https://github.com/raiderrobert/django-multiurl',
    download_url='https://github.com/raiderrobert/django-multiurl/tarball/v1.1.0',
    author='Jacob Kaplan-Moss and Robert Roskam',
    author_email='raiderrobert@gmail.com',
    install_requires=['django>=1.5'],
    keywords='django urls',
    classifiers=[
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
    ],
)
