===============================
Testing with ``aspectlib.test``
===============================

Spy & mock toolkit: ``record``/``mock`` decorators
==================================================

.. highlights::

    Lightweight spies and mock responses


Example usage, suppose you want to test this class:

    >>> class ProductionClass(object):
    ...     def method(self):
    ...         return 'stuff'
    >>> real = ProductionClass()

With :obj:`aspectlib.test.mock` and :obj:`aspectlib.test.record`::

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

Capture-replay toolkit: ``Story`` and ``Replay``
================================================

.. highlights::

    Elaborate tools for testing difficult code

Writing tests using the :obj:`Story <aspectlib.test.Story>` is viable when neither `integration tests
<http://en.wikipedia.org/wiki/Integration_testing>`_ or `unit tests <http://en.wikipedia.org/wiki/Unit_testing>`_ seem
adequate:

    * Integration tests are too difficult to integrate in your test harness due to automation issues, permissions or
      plain lack of performance.
    * Unit tests are too difficult to write due to design issues (like too many dependencies, dependency injects is too
      hard etc) or take too much time to write to get good code coverage.

The :obj:`Story <aspectlib.test.Story>` is the middle-ground, bringing those two types of testing closer. It allows you
to start with `integration tests` and later `mock`/`stub` with great ease all the dependencies.

An example: mocking out an external system
------------------------------------------

TODO
