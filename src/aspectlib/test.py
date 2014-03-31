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

from aspectlib import mimic
from aspectlib import weave

__all__ = 'mock', 'record'

Call = namedtuple('Call', ('self', 'args', 'kwargs'))


def mock(return_value, call=False):
    """
    Factory for a decorator that makes the function return a given `return_value`.

    :param return_value: Value to return from the wrapper.
    :param bool call: If ``True``, call the decorated function. (default: ``False``)
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

class RecordingWrapper(object):
    """
    Function wrapper that has a `calls` attribute.

    :param function wrapped: Function to be wrapped
    :param function wrapped: Wrapper function
    :param list calls: Instance to put in the `.calls` attribute.
    """
    def __init__(self, wrapped, history, call, binding=None):
        mimic(self, wrapped)
        self.__wrapped = wrapped
        self.__entanglement = None
        self.__call = call
        self.__binding = binding
        self.calls = history

    def __call__(self, *args, **kwargs):
        self.calls.append(Call(self.__binding, args, kwargs))
        if self.__call:
            return self.__wrapped(*args, **kwargs)

    def __get__(self, instance, owner):
        return RecordingWrapper(self.__wrapped.__get__(instance, owner), self.calls, self.__call, instance)

    def __enter__(self):
        self.__entanglement = weave(self.__wrapped, lambda _: self)
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()

def record(func=None, call=False, history=None):
    """
    Factory or decorator (depending if `func` is initially given).

    :param list history:
        An object where the `Call` objects are appended. If not given a new list object will be created.

    :param bool call:
        If ``True`` the `func` will be called. (default: ``False``)

    :returns:
        A wrapper that has a `calls` property.

    The decorator returns a wrapper that records all calls made to `func`. The history is available as a ``call``
    property. If access to the function is too hard then you need to specify the history manually.

    Example::

        >>> @record
        ... def a():
        ...     pass
        >>> a(1, 2, 3, b='c')
        >>> a.calls
        [Call(self=None, args=(1, 2, 3), kwargs={'b': 'c'})]


    Or, with your own history list::

        >>> calls = []
        >>> @record(history=calls)
        ... def a():
        ...     pass
        >>> a(1, 2, 3, b='c')
        >>> a.calls
        [Call(self=None, args=(1, 2, 3), kwargs={'b': 'c'})]
        >>> calls is a.calls
        True

    """
    if func:
        return RecordingWrapper(func, list() if history is None else history, call)
    else:
        return partial(record, call=call, history=history)
