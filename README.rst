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
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/python-aspectlib/badge/?style=flat
    :target: https://readthedocs.org/projects/python-aspectlib
    :alt: Documentation Status

.. |travis| image:: https://api.travis-ci.org/ionelmc/python-aspectlib.svg?branch=master
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

.. |codecov| image:: https://codecov.io/gh/ionelmc/python-aspectlib/branch/master/graphs/badge.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/ionelmc/python-aspectlib

.. |version| image:: https://img.shields.io/pypi/v/aspectlib.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/aspectlib

.. |wheel| image:: https://img.shields.io/pypi/wheel/aspectlib.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/aspectlib

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/aspectlib.svg
    :alt: Supported versions
    :target: https://pypi.org/project/aspectlib

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/aspectlib.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/aspectlib

.. |commits-since| image:: https://img.shields.io/github/commits-since/ionelmc/python-aspectlib/v1.4.2.svg
    :alt: Commits since latest release
    :target: https://github.com/ionelmc/python-aspectlib/compare/v1.4.2...master



.. end-badges

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired. It includes tools for debugging and testing: simple mock/record and a complete
capture/replay framework.

* Free software: BSD 2-Clause License

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
