============
Introduction
============

`aspectlib` provides two core tools to do `AOP <http://en.wikipedia.org/wiki/Aspect-oriented_programming>`_: Aspects and
a weaver.

The aspect
==========

An *aspect* can be created by decorating a generator with an :obj:`~aspectlib.Aspect`. The generator yields *advices* -
simple behavior changing instructions.

An :obj:`~aspectlib.Aspect` instance is a simple function decorator. Decorating a function with an *aspect* will change
the function's behavior according to the *advices* yielded by the generator.

Example:

.. code-block:: python

    @aspectlib.Aspect
    def strip_return_value():
        result = yield aspectlib.Proceed
        yield aspectlib.Return(result.strip())

    @strip_return_value
    def read(name):
        return open(name).read()

.. _advices:

Advices
-------

You can use these *advices*:

* :obj:`~aspectlib.Proceed` or ``None`` - Calls the wrapped function with the default arguments. The *yield* returns
  the function's return value or raises an exception. Can be used multiple times (will call the function
  multiple times).
* :obj:`~aspectlib.Proceed` ``(*args, **kwargs)`` - Same as above but with different arguments.
* :obj:`~aspectlib.Return` - Makes the wrapper return ``None`` instead. If ``aspectlib.Proceed`` was never used then
  the wrapped function is not called. After this the generator is closed.
* :obj:`~aspectlib.Return` ``(value)`` - Same as above but returns the given ``value`` instead of ``None``.
* ``raise exception`` - Makes the wrapper raise an exception.

The weaver
==========

Patches classes and functions with the given *aspect*. When used with a class it will patch all the methods. In AOP
parlance these patched functions and methods are referred to as *cut-points*.

Returns a :class:`~aspectlib.Rollback` object that can be used a context manager.
It will undo all the changes at the end of the context.

Example:

.. code-block:: python
    :emphasize-lines: 5

    @aspectlib.Aspect
    def mock_open():
        yield aspectlib.Return(StringIO("mystuff"))

    with aspectlib.weave(open, mock_open):
        assert open("/doesnt/exist.txt").read() == "mystuff"

You can use :func:`aspectlib.weave` on: classes, instances, builtin functions, module level functions, methods,
classmethods, staticmethods, instance methods etc.
