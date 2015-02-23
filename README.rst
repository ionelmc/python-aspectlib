================
python-aspectlib
================

| |docs| |travis| |appveyor| |coveralls| |landscape| |scrutinizer|
| |version| |downloads| |wheel| |supported-versions| |supported-implementations|

.. |docs| image:: https://readthedocs.org/projects/python-aspectlib/badge/?style=flat
    :target: https://readthedocs.org/projects/python-aspectlib
    :alt: Documentation Status

.. |travis| image:: http://img.shields.io/travis/ionelmc/python-aspectlib/master.png?style=flat
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/python-aspectlib

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/ionelmc/python-aspectlib?branch=master
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ionelmc/python-aspectlib

.. |coveralls| image:: http://img.shields.io/coveralls/ionelmc/python-aspectlib/master.png?style=flat
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib

.. |landscape| image:: https://landscape.io/github/ionelmc/python-aspectlib/master/landscape.svg?style=flat
    :target: https://landscape.io/github/ionelmc/python-aspectlib/master
    :alt: Code Quality Status

.. |version| image:: http://img.shields.io/pypi/v/aspectlib.png?style=flat
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/aspectlib

.. |downloads| image:: http://img.shields.io/pypi/dm/aspectlib.png?style=flat
    :alt: PyPI Package monthly downloads
    :target: https://pypi.python.org/pypi/aspectlib

.. |wheel| image:: https://pypip.in/wheel/aspectlib/badge.png?style=flat
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/aspectlib

.. |supported-versions| image:: https://pypip.in/py_versions/aspectlib/badge.png?style=flat
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/aspectlib

.. |supported-implementations| image:: https://pypip.in/implementation/aspectlib/badge.png?style=flat
    :alt: Supported imlementations
    :target: https://pypi.python.org/pypi/aspectlib

.. |scrutinizer| image:: https://img.shields.io/scrutinizer/g/ionelmc/python-aspectlib/master.png?style=flat
    :alt: Scrtinizer Status
    :target: https://scrutinizer-ci.com/g/ionelmc/python-aspectlib/

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired. It includes tools for debugging and testing: simple mock/record and a complete
capture/replay framework.


Documentation
=============

Docs are hosted at readthedocs.org: `python-aspectlib docs <http://python-aspectlib.readthedocs.org/en/latest/>`_.

Implementation status
=====================

Weaving functions, methods, instances and classes is completed.

Pending:

* *"Concerns"* (see `docs/todo.rst`)

If ``aspectlib.weave`` doesn't work for your scenario please report a bug !

Requirements
============

:OS: Any
:Runtime: Python 2.6, 2.7, 3.3, 3.4 or PyPy

Python 3.2, 3.1 and 3.0 are *NOT* supported (some objects are too crippled).

Similar projects
================

* `function_trace <https://github.com/RedHatQE/function_trace>`_ - extremely simple
