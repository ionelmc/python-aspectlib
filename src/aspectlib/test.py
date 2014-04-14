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
from inspect import isclass

from aspectlib import ALL_METHODS
from aspectlib import mimic
from aspectlib import weave

__all__ = 'mock', 'record', "Story"

Call = namedtuple('Call', ('self', 'args', 'kwargs'))
CallEx = namedtuple('CallEx', ('self', 'name', 'args', 'kwargs'))
Result = namedtuple('Result', ('self', 'args', 'kwargs', 'result', 'exception'))
ResultEx = namedtuple('ResultEx', ('self', 'name', 'args', 'kwargs', 'result', 'exception'))


def qualname(obj):
    return '%s.%s' % (obj.__module__, obj.__name__)


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


class RecordingFunctionWrapper(object):
    """
    Function wrapper that records calls and can be used as an weaver context manager.

    See :obj:`aspectlib.test.record` for arguments.
    """

    def __init__(self, wrapped, iscalled=True, calls=None, callback=None, extended=False, results=False,
                 recurse_lock=None, binding=None):
        assert not results or iscalled, "`iscalled` must be True if `results` is True"
        mimic(self, wrapped)
        self.__wrapped = wrapped
        self.__name = qualname(wrapped)
        self.__entanglement = None
        self.__iscalled = iscalled
        self.__binding__ = binding
        self.__callback__ = callback
        self.__extended = extended
        self.__results = results
        self.__recurse_lock = recurse_lock
        self.calls = [] if not callback and calls is None else calls

    def __call__(self, *args, **kwargs):
        record = not self.__recurse_lock or self.__recurse_lock.acquire(False)
        try:
            if self.__results:
                try:
                    result = self.__wrapped(*args, **kwargs)
                except Exception as exc:
                    if record:
                        self.__record(args, kwargs, None, exc)
                    raise
                else:
                    if record:
                        self.__record(args, kwargs, result, None)
                    return result
            else:
                if record:
                    self.__record(args, kwargs)
                if self.__iscalled:
                    return self.__wrapped(*args, **kwargs)
        finally:
            if record and self.__recurse_lock:
                self.__recurse_lock.release()

    def __record(self, args, kwargs, *response):
        if self.__callback__ is not None:
            self.__callback__(self.__binding__, self.__name, args, kwargs, *response)
        if self.calls is not None:
            if self.__extended:
                self.calls.append((ResultEx if response else CallEx)(
                    self.__binding__, self.__name, args, kwargs, *response
                ))
            else:
                self.calls.append((Result if response else Call)(
                    self.__binding__, args, kwargs, *response
                ))

    def __get__(self, instance, owner):
        return RecordingFunctionWrapper(
            self.__wrapped.__get__(instance, owner),
            iscalled=self.__iscalled,
            calls=self.calls,
            callback=self.__callback__,
            extended=self.__extended,
            results=self.__results,
            binding=instance,
        )

    def __enter__(self):
        self.__entanglement = weave(self.__wrapped, lambda _: self)
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()


def record(func=None, **options):
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
    :param bool results:
        If ``True`` the results (and exceptions) will also be included in the call list. (default: ``False``)
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
        return RecordingFunctionWrapper(
            func,
            **options
        )
    else:
        return partial(record, **options)


class Story(object):
    def __init__(self, target, lazy=False):
        self.__target = target
        self.calls = {}
        self.ids = {}

    def __enter__(self):
        self.__entanglement = weave(
            self.__target,
            partial(StoryFunctionWrapper, story=self),
            methods=ALL_METHODS,
        )
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()

class StoryFunctionWrapper(object):
    def __init__(self, wrapped, story, binding=None, owner=None):
        self.__wrapped = wrapped
        self.__name = wrapped.__name__
        self.__qualname = qualname(wrapped)
        self.__story = story
        self.__binding = binding
        self.__owner = owner

    def __call__(self, *args, **kwargs):
        story = self.__story
        if self.__binding is None:
            pk = self.__qualname, args, frozenset(kwargs.items())
            return StoryResultWrapper(partial(self.__save, story.calls, pk))
        else:
            if self.__name == '__init__':
                pk = qualname(self.__owner), args, frozenset(kwargs.items())
                story.ids[self.__binding] = self.__save(story.calls, pk, {})
            else:
                pk = self.__name, args, frozenset(kwargs.items())
                return StoryResultWrapper(partial(self.__save, story.ids[self.__binding], pk))

    def __save(self, calls, pk, response):
        assert pk not in calls, "Story creation inconsistency. There is already a call cache for %r and it's: %r." % (pk, calls[pk])
        calls[pk] = response
        return response

    def __get__(self, binding, owner):
        return StoryFunctionWrapper(
            self.__wrapped.__get__(binding, owner),
            story=self.__story,
            binding=binding,
            owner=owner,
        )


class StoryResultWrapper(object):
    __slots__ = '__recorder__'

    def __init__(self, recorder):
        self.__recorder__ = recorder

    def __eq__(self, result):
        self.__recorder__((result, None))

    def __pow__(self, exception):
        if not (isinstance(exception, BaseException) or isclass(exception) and issubclass(exception, BaseException)):
            raise RuntimeError("Value %r must be an exception type or instance." % exception)
        self.__recorder__((None, exception))

    def __unsupported__(self, *args):
        raise TypeError("Unsupported operation. Only `==` (for results) and `**` (for exceptions) can be used.")

    for mm in (
        '__add__', '__sub__', '__mul__', '__floordiv__', '__mod__', '__divmod__', '__lshift__', '__rshift__', '__and__',
        '__xor__', '__or__', '__div__', '__truediv__', '__radd__', '__rsub__', '__rmul__', '__rdiv__', '__rtruediv__',
        '__rfloordiv__', '__rmod__', '__rdivmod__', '__rpow__', '__rlshift__', '__rrshift__', '__rand__', '__rxor__',
        '__ror__', '__iadd__', '__isub__', '__imul__', '__idiv__', '__itruediv__', '__ifloordiv__', '__imod__',
        '__ipow__', '__ilshift__', '__irshift__', '__iand__', '__ixor__', '__ior__', '__neg__', '__pos__', '__abs__',
        '__invert__', '__complex__', '__int__', '__long__', '__float__', '__oct__', '__hex__', '__index__',
        '__coerce__', '__getslice__', '__setslice__', '__delslice__', '__len__', '__getitem__', '__reversed__',
        '__contains__', '__call__', '__lt__', '__le__', '__ne__', '__gt__', '__ge__', '__cmp__', '__rcmp__',
        '__nonzero__',
    ):
        exec ("%s = __unsupported__" % mm)
