aspectlib.test
==============

This module aims to be a lightweight and flexible alternative to the popular `mock <https://pypi.python.org/pypi/mock>`_
framework.

.. autosummary::
    :nosignatures:

    aspectlib.test.record
    aspectlib.test.mock
    aspectlib.test.Story
    aspectlib.test.Replay


Spy & mock toolkit: ``record``/``mock`` decorators
--------------------------------------------------

.. highlights::

    Lightweight spies and mock responses


Example usage, suppose you want to test this class:

    >>> class ProductionClass(object):
    ...     def method(self):
    ...         return 'stuff'
    >>> real = ProductionClass()

With :mod:`aspectlib.test`::

    >>> from aspectlib import weave, test
    >>> patch = weave(real.method, [test.mock(3), test.record])
    >>> real.method(3, 4, 5, key='value')
    3
    >>> assert real.method.calls == [(real, (3, 4, 5), {'key': 'value'})]

As a bonus, you have an easy way to rollback all the mess::

    >>> patch.rollback()
    >>> real.method()
    'stuff'

With ``mock``::

    >>> from mock import Mock
    >>> real = ProductionClass()
    >>> real.method = Mock(return_value=3)
    >>> real.method(3, 4, 5, key='value')
    3
    >>> real.method.assert_called_with(3, 4, 5, key='value')

.. automodule:: aspectlib.test
    :members: record, mock

Capture-replay toolkit: ``Story`` and ``Replay``
------------------------------------------------

.. highlights::

    Elaborate tools for testing difficult code

.. automodule:: aspectlib.test
    :members: Story

.. autoclass:: Replay(?)
    :members:
