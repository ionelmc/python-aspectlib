================
python-aspectlib
================

+--------------------+--------------------+---------------------+
| | |travis-badge|   | |                  | | |version-badge|   |
| | |appveyor-badge| | | |coverage-badge| | | |downloads-badge| |
+--------------------+--------------------+---------------------+

.. |travis-badge| image:: http://img.shields.io/travis/ionelmc/python-aspectlib.png?style=flat
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/ionelmc/python-aspectlib
.. |appveyor-badge| image:: https://ci.appveyor.com/api/projects/status/u2f05p7rmd5hsixi
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/ionelmc/python-aspectlib
.. |coverage-badge| image:: http://img.shields.io/coveralls/ionelmc/python-aspectlib.png?style=flat
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib
.. |version-badge| image:: http://img.shields.io/pypi/v/aspectlib.png?style=flat
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/aspectlib
.. |downloads-badge| image:: http://img.shields.io/pypi/dm/aspectlib.png?style=flat
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
