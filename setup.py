# -*- encoding: utf8 -*-
from setuptools import setup, find_packages

import os

setup(
    name="aspectlib",
    version="0.7.0",
    url='https://github.com/ionelmc/python-aspectlib',
    download_url='',
    license='BSD',
    description="Aspect-Oriented Programming toolkit.",
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Ionel Cristian Mărieș',
    author_email='contact@ionelmc.ro',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    keywords=[
        'python', 'aop', 'aspects', 'aspect oriented programming', 'decorators', 'patch', 'monkeypatch', 'weave',
        'debug', 'log', 'tests', 'mock'
    ],
    install_requires=[
        'wrapt>=1.6.0',
    ],
    extras_require={
    }
)
