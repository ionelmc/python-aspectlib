aspectlib.debug
===============

.. autosummary::
    :nosignatures:

    aspectlib.debug.log
    aspectlib.debug.format_stack
    aspectlib.debug.frame_iterator
    aspectlib.debug.strip_non_ascii

.. automodule:: aspectlib.debug
    :members:
    :exclude-members: log

.. autofunction:: log

    .. versionchanged:: 0.5.0

        Renamed `arguments` to `call_args`.
        Renamed `arguments_repr` to `call_args_repr`.
        Added `call` option.
        Fixed issue with logging from old-style methods (object name was a generic "instance").

