aspectlib
=========

.. highlights::

    Safe toolkit for writing decorators (hereby called **aspects**)

.. autosummary::
    :nosignatures:

    aspectlib.Aspect
    aspectlib.Rollback
    aspectlib.Proceed
    aspectlib.Return

.. highlights::

    Power tools for patching functions (hereby glorified as **weaving**)

.. autosummary::
    :nosignatures:

    aspectlib.ALL_METHODS
    aspectlib.NORMAL_METHODS
    aspectlib.weave


Reference
---------


.. automodule:: aspectlib
    :members:
    :exclude-members: weave, Aspect

.. autoclass:: Aspect

    You can use these *advices*:

    * :obj:`~aspectlib.Proceed` or ``None`` - Calls the wrapped function with the default arguments. The *yield* returns
      the function's return value or raises an exception. Can be used multiple times (will call the function
      multiple times).
    * :obj:`~aspectlib.Proceed` ``(*args, **kwargs)`` - Same as above but with different arguments.
    * :obj:`~aspectlib.Return` - Makes the wrapper return ``None`` instead. If ``aspectlib.Proceed`` was never used then
      the wrapped function is not called. After this the generator is closed.
    * :obj:`~aspectlib.Return` ``(value)`` - Same as above but returns the given ``value`` instead of ``None``.
    * ``raise exception`` - Makes the wrapper raise an exception.

    .. note::

        The Aspect will correctly handle generators and coroutines (consume them, capture result).

        Example::

            >>> from aspectlib import Aspect
            >>> @Aspect
            ... def log_errors(*args, **kwargs):
            ...     try:
            ...         yield
            ...     except Exception as exc:
            ...         print("Raised %r for %s/%s" % (exc, args, kwargs))
            ...         raise

        Will work as expected with generators (and coroutines):

        .. sourcecode:: pycon

            >>> @log_errors
            ... def broken_generator():
            ...     yield 1
            ...     raise RuntimeError()
            >>> raises(RuntimeError, lambda: list(broken_generator()))
            Raised RuntimeError() for ()/{}
            ...

            >>> @log_errors
            ... def broken_function():
            ...     raise RuntimeError()
            >>> raises(RuntimeError, broken_function)
            Raised RuntimeError() for ()/{}
            ...


.. autoclass:: Rollback

    .. automethod:: __enter__

        Returns self.

    .. automethod:: __exit__

        Performs the rollback.

    .. automethod:: rollback

        Alias of ``__exit__``.

    .. automethod:: __call__

        Alias of ``__exit__``.

.. autodata:: ALL_METHODS
    :annotation: Weave all magic methods. Can be used as the value for methods argument in weave.

.. autodata:: NORMAL_METHODS
    :annotation: Only weave non-magic methods. Can be used as the value for methods argument in weave.

.. autofunction:: weave(target, aspect[, subclasses=True, methods=NORMAL_METHODS, lazy=False, aliases=True])
