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
"""
from collections import namedtuple
from functools import partial
from functools import wraps

from aspectlib import mimic
from aspectlib import weave

__all__ = 'mock', 'record'

Call = namedtuple('Call', ('self', 'args', 'kwargs'))
CallEx = namedtuple('Call', ('self', 'name', 'args', 'kwargs'))


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
    def __init__(self, wrapped, wrapped_iscalled, calls=None, callback=None, extended=False, binding=None):
        mimic(self, wrapped)
        self.__wrapped = wrapped
        self.__entanglement = None
        self.__wrapped_iscalled = wrapped_iscalled
        self.__binding = binding
        self.__callback = callback
        self.__extended = extended
        self.calls = calls
        if calls is None and callback is None:
            raise RuntimeError("Can't have both calls (%r) and callback (%r) be None" % (calls, callback))

    def __call__(self, *args, **kwargs):
        if self.calls is not None:
            if self.__extended:
                self.calls.append(CallEx(self.__binding, self.__wrapped.__name__, args, kwargs))
            else:
                self.calls.append(Call(self.__binding, args, kwargs))
        if self.__callback is not None:
            self.__callback(self.__binding, self.__wrapped, args, kwargs)
        if self.__wrapped_iscalled:
            return self.__wrapped(*args, **kwargs)

    def __get__(self, instance, owner):
        return RecordingWrapper(
            self.__wrapped.__get__(instance, owner),
            self.__wrapped_iscalled,
            calls=self.calls,
            callback=self.__callback,
            extended=self.__extended,
            binding=instance,
        )

    def __enter__(self):
        self.__entanglement = weave(self.__wrapped, lambda _: self)
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()

def record(func=None, iscalled=True, calls=None, callback=None, extended=False):
    """
    Factory or decorator (depending if `func` is initially given).

    :param list callback:
        An a callable that is to be called with ``instance, function, args, kwargs``.
    :param list calls:
        An object where the `Call` objects are appended. If not given and ``callback`` is not specified then a new list
        object will be created.
    :param bool iscalled:
        If ``True`` the `func` will be called. (default: ``False``)
    :param bool extended:
        If ``True`` the `func`'s ``__name__`` will also be included in the call list. (default: ``False``)
    :returns:
        A wrapper that has a `calls` property.

    The decorator returns a wrapper that records all calls made to `func`. The history is available as a ``call``
    property. If access to the function is too hard then you need to specify the history manually.

    Example::

        >>> @record
        ... def a(x, y, a, b):
        ...     pass
        >>> a(1, 2, 3, b='c')
        >>> a.calls
        [Call(self=None, args=(1, 2, 3), kwargs={'b': 'c'})]


    Or, with your own history list::

        >>> calls = []
        >>> @record(calls=calls)
        ... def a(x, y, a, b):
        ...     pass
        >>> a(1, 2, 3, b='c')
        >>> a.calls
        [Call(self=None, args=(1, 2, 3), kwargs={'b': 'c'})]
        >>> calls is a.calls
        True


    .. versionchanged:: 0.9.0

        Renamed `history` option to `calls`.
        Renamed `call` option to `iscalled`.
        Added `callback` option.
        Added `extended` option.
    """
    if func:
        return RecordingWrapper(
            func,
            iscalled,
            calls=(list() if not callback and calls is None else calls),
            callback=callback,
            extended=extended,
        )
    else:
        return partial(record, iscalled=iscalled, calls=calls, callback=callback, extended=extended)
