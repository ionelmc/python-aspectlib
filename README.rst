========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |coveralls| |codecov|
        | |landscape| |scrutinizer| |codacy| |codeclimate|
    * - package
      - |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/python-aspectlib/badge/?style=flat
    :target: https://readthedocs.org/projects/python-aspectlib
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/ionelmc/python-aspectlib.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/python-aspectlib

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/ionelmc/python-aspectlib?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ionelmc/python-aspectlib

.. |requires| image:: https://requires.io/github/ionelmc/python-aspectlib/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/ionelmc/python-aspectlib/requirements/?branch=master

.. |coveralls| image:: https://coveralls.io/repos/ionelmc/python-aspectlib/badge.svg?branch=master&service=github
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib

.. |codecov| image:: https://codecov.io/github/ionelmc/python-aspectlib/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ionelmc/python-aspectlib

.. |landscape| image:: https://landscape.io/github/ionelmc/python-aspectlib/master/landscape.svg?style=flat
    :target: https://landscape.io/github/ionelmc/python-aspectlib/master
    :alt: Code Quality Status

.. |codacy| image:: https://img.shields.io/codacy/9557dc3ca38f43bcac85240f73e1985a.svg?style=flat
    :target: https://www.codacy.com/app/ionelmc/python-aspectlib
    :alt: Codacy Code Quality Status

.. |codeclimate| image:: https://codeclimate.com/github/ionelmc/python-aspectlib/badges/gpa.svg
   :target: https://codeclimate.com/github/ionelmc/python-aspectlib
   :alt: CodeClimate Quality Status

.. |version| image:: https://img.shields.io/pypi/v/aspectlib.svg?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/aspectlib

.. |downloads| image:: https://img.shields.io/pypi/dm/aspectlib.svg?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/aspectlib

.. |wheel| image:: https://img.shields.io/pypi/wheel/aspectlib.svg?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/aspectlib

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/aspectlib.svg?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/aspectlib

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/aspectlib.svg?style=flat
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/aspectlib

.. |scrutinizer| image:: https://img.shields.io/scrutinizer/g/ionelmc/python-aspectlib/master.svg?style=flat
    :alt: Scrutinizer Status
    :target: https://scrutinizer-ci.com/g/ionelmc/python-aspectlib/


.. end-badges

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired. It includes tools for debugging and testing: simple mock/record and a complete
capture/replay framework.

* Free software: BSD license

Installation
============

::

    pip install aspectlib

Documentation
=============

Docs are hosted at readthedocs.org: `python-aspectlib docs <http://python-aspectlib.readthedocs.org/en/latest/>`_.

Implementation status
=====================

Weaving functions, methods, instances and classes is completed.

Pending:

* *"Concerns"* (see `docs/todo.rst`)

If ``aspectlib.weave`` doesn't work for your scenario please report a bug!

Requirements
============

:OS: Any
:Runtime: Python 2.6, 2.7, 3.3, 3.4 or PyPy

Python 3.2, 3.1 and 3.0 are *NOT* supported (some objects are too crippled).

Similar projects
================

* `function_trace <https://github.com/RedHatQE/function_trace>`_ - extremely simple
