aspectlib
=========

.. autosummary::
    :nosignatures:

    aspectlib.ALL_METHODS
    aspectlib.NORMAL_METHODS
    aspectlib.weave
    aspectlib.Rollback
    aspectlib.Aspect
    aspectlib.Proceed
    aspectlib.Return

.. automodule:: aspectlib
    :members:
    :exclude-members: weave

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
