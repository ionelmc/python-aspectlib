"""
This module is designed to be a lightweight, orthogonal and easy to learn replacement for the popular `mock
<https://pypi.python.org/pypi/mock>`_ framework.

Example usage, suppose you want to test this class:

    >>> class ProductionClass(object):
    ...     def method(self):
    ...         return 'stuff'
    >>> real = ProductionClass()

With :mod:`aspectlib.test`::

    >>> from aspectlib import weave, test
    >>> patch = weave(real.method, [test.mock(3), test.record(call=True)])
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


"""
from collections import namedtuple
from functools import partial
from functools import wraps

from wrapt.decorators import FunctionWrapper, BoundFunctionWrapper

import aspectlib

__all__ = 'mock', 'record'

Call = namedtuple('Call', ('self', 'args', 'kwargs'))


def mock(return_value, call=False):
    """
    Factory for a decorator that makes the function return a given `return_value`.

    :param return_value: Value to return from the wrapper.
    :param bool call: If ``True``, call the decorated function.
    :returns: A decorator.
    """
    def mock_decorator(func):
        @wraps(func)
        def mock_wrapper(*args, **kwargs):
            if call:
                func(*args, **kwargs)
            return return_value
        return mock_wrapper
    return mock_decorator

class BoundRecordingWrapper(BoundFunctionWrapper):
    calls = None

    def __init__(self, wrapped, instance, wrapper, enabled, binding, parent):
        super(BoundRecordingWrapper, self).__init__(wrapped, instance, wrapper, enabled, binding, parent)
        self.calls = parent.calls

class RecordingWrapper(FunctionWrapper):
    """
    Function wrapper that has a `calls` attribute.

    :param function wrapped: Function to be wrapped
    :param function wrapped: Wrapper function
    :param list calls: Instance to put in the `.calls` attribute.
    """
    calls = None
    __bound_function_wrapper__ = BoundRecordingWrapper

    def __init__(self, wrapped, wrapper, calls):
        super(RecordingWrapper, self).__init__(wrapped, wrapper)
        self.calls = calls

    def __enter__(self):
        self._self_entanglement = aspectlib.weave(self.__wrapped__, lambda _: self)
        return self

    def __exit__(self, *args):
        self._self_entanglement.rollback()


def record(func=None, call=False, history=None):
    """
    Factory or decorator (depending if `func` is initially given).

    The decorator returns a wrapper that records all calls made to `func`.

    :param list history:
        An object where the `Call` objects are appended. If not given a new list object will be created.

    :param bool call:
        If ``True`` the `func` will be called.

    :returns:
        A wrapper that has a `calls` property.
    """
    def record_decorator(func):
        calls = list() if history is None else history

        def record_wrapper(wrapped, instance, args, kwargs):
            calls.append(Call(instance, args, kwargs))
            if call:
                return wrapped(*args, **kwargs)
        recorded = RecordingWrapper(func, record_wrapper, calls)
        return recorded

    if func:
        return record_decorator(func)
    else:
        return partial(record, call=call, history=history)
