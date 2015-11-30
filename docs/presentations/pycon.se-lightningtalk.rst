.. raw:: html

    <style type="text/css">
        h1 {page-break-before: always; }
        .section:first-of-type h1 {page-break-before: avoid; }
    </style>

Does this look familiar ?
=========================

.. sourcecode:: pycon

    >>> from functools import wraps
    >>> def log_errors(func):
    ...     @wraps(func)
    ...     def log_errors_wrapper(*args, **kwargs):
    ...         try:
    ...             return func(*args, **kwargs)
    ...         except Exception as exc:
    ...             print("Raised %r for %s/%s" % (exc, args, kwargs))
    ...             raise
    ...     return log_errors_wrapper

.. sourcecode:: pycon

    >>> @log_errors
    ... def broken_function():
    ...     raise RuntimeError()
    >>> from pytest import raises
    >>> t = raises(RuntimeError, broken_function)
    Raised RuntimeError() for ()/{}

Not very nice
=============

* Boiler plate
* What if you use it on a generator ?

What if you use it on a generator ?
===================================

.. sourcecode:: pycon

    >>> @log_errors
    ... def broken_generator():
    ...     yield 1
    ...     raise RuntimeError()

    >>> t = raises(RuntimeError, lambda: list(broken_generator()))

Dooh! No output.

How to fix it ?
===============

.. sourcecode:: pycon

    >>> from inspect import isgeneratorfunction
    >>> def log_errors(func):
    ...     if isgeneratorfunction(func): # because you can't both return and yield in the same function
    ...         @wraps(func)
    ...         def log_errors_wrapper(*args, **kwargs):
    ...             try:
    ...                 for item in func(*args, **kwargs):
    ...                     yield item
    ...             except Exception as exc:
    ...                 print("Raised %r for %s/%s" % (exc, args, kwargs))
    ...                 raise
    ...     else:
    ...         @wraps(func)
    ...         def log_errors_wrapper(*args, **kwargs):
    ...             try:
    ...                 return func(*args, **kwargs)
    ...             except Exception as exc:
    ...                 print("Raised %r for %s/%s" % (exc, args, kwargs))
    ...                 raise
    ...     return log_errors_wrapper

Now it works:

.. sourcecode:: pycon

    >>> @log_errors
    ... def broken_generator():
    ...     yield 1
    ...     raise RuntimeError()

    >>> t = raises(RuntimeError, list, broken_generator())
    Raised RuntimeError() for ()/{}

**Note:** Doesn't actually work for coroutines ... it would involve more code to handle edge cases.

The alternative, use ``aspectlib``
==================================

.. sourcecode:: pycon

    >>> from aspectlib import Aspect
    >>> @Aspect
    ... def log_errors(*args, **kwargs):
    ...     try:
    ...         yield
    ...     except Exception as exc:
    ...         print("Raised %r for %s/%s" % (exc, args, kwargs))
    ...         raise

Works as expected with generators:

.. sourcecode:: pycon

    >>> @log_errors
    ... def broken_generator():
    ...     yield 1
    ...     raise RuntimeError()
    >>> t = raises(RuntimeError, lambda: list(broken_generator()))
    Raised RuntimeError() for ()/{}

    >>> @log_errors
    ... def broken_function():
    ...     raise RuntimeError()
    >>> t = raises(RuntimeError, broken_function)
    Raised RuntimeError() for ()/{}

``aspectlib``
=============

* **This presentation**:

    https://github.com/ionelmc/python-aspectlib/tree/master/docs/presentations

* ``aspectlib`` **does many more things, check it out**:

    http://python-aspectlib.readthedocs.org/en/latest/
