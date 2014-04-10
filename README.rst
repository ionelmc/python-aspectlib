================
python-aspectlib
================

.. image:: https://secure.travis-ci.org/ionelmc/python-aspectlib.png
    :alt: Build Status
    :target: https://travis-ci.org/ionelmc/python-aspectlib

.. image:: https://coveralls.io/repos/ionelmc/python-aspectlib/badge.png?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib

.. image:: https://pypip.in/d/aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/aspectlib

.. image:: https://pypip.in/v/aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/aspectlib

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired.

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
