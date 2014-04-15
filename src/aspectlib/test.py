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
import warnings
from collections import defaultdict
from collections import namedtuple
from functools import partial
from functools import wraps
from inspect import isclass
from operator import itemgetter

from aspectlib import ALL_METHODS
from aspectlib import mimic
from aspectlib import weave

from .utils import camelcase_to_underscores
from .utils import qualname

try:
    from dummy_thread import allocate_lock
except ImportError:
    from _dummy_thread import allocate_lock
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

__all__ = 'mock', 'record', "Story"

Call = namedtuple('Call', ('self', 'args', 'kwargs'))
CallEx = namedtuple('CallEx', ('self', 'name', 'args', 'kwargs'))
Result = namedtuple('Result', ('self', 'args', 'kwargs', 'result', 'exception'))
ResultEx = namedtuple('ResultEx', ('self', 'name', 'args', 'kwargs', 'result', 'exception'))


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
        self.__callback = callback
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
        if self.__callback is not None:
            self.__callback(self.__binding__, self.__name, args, kwargs, *response)
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
            callback=self.__callback,
            extended=self.__extended,
            results=self.__results,
            binding=instance,
        )

    def __enter__(self):
        self.__entanglement = weave(self.__wrapped, lambda _: self)
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()


def record(func=None, recurse_lock_factory=allocate_lock, **options):
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
            recurse_lock=recurse_lock_factory(),
            **options
        )
    else:
        return partial(record, **options)


class StoryFunctionWrapper(object):
    def __init__(self, wrapped, story, binding=None, owner=None):
        self._wrapped = wrapped
        self._name = wrapped.__name__
        self._qualname = qualname(wrapped)
        self._story = story
        self._binding = binding
        self._owner = owner

    def __call__(self, *args, **kwargs):
        story = self._story
        if self._binding is None:
            pk = self._qualname, args, frozenset(kwargs.items())
            return StoryResultWrapper(partial(self._save, story.calls, pk))
        else:
            if self._name == '__init__':
                pk = qualname(self._owner), args, frozenset(kwargs.items())
                story._ids[self._binding] = self._save(story.calls, pk, {})
            else:
                pk = self._name, args, frozenset(kwargs.items())
                return StoryResultWrapper(partial(self._save, story._ids[self._binding], pk))

    def _save(self, calls, pk, response):
        assert pk not in calls, "Story creation inconsistency. There is already a call cache for %r and it's: %r." % (pk, calls[pk])
        calls[pk] = response
        return response

    def __get__(self, binding, owner):
        return type(self)(
            self._wrapped.__get__(binding, owner),
            story=self._story,
            binding=binding,
            owner=owner,
        )


class unexpected(dict):
    def __repr__(self):
        return "unexpected(%s)" % super(unexpected, self).__repr__()


class ReplayFunctionWrapper(StoryFunctionWrapper):
    def __call__(self, *args, **kwargs):
        story = self._story
        if self._binding is None:
            pk = self._qualname, args, frozenset(kwargs.items())
            calls = story.calls
        else:
            if self._name == '__init__':
                pk = qualname(self._owner), args, frozenset(kwargs.items())
                calls = story.calls
                if pk in calls.expected:
                    story._ids[self._binding] = ReplayPair(calls.expected[pk], calls.unexpected.setdefault(pk, {}))
                    return
                elif story._proxy:
                    story._ids[self._binding] = ReplayPair({}, calls.unexpected.setdefault(pk, unexpected()))
                    return self._wrapped(*args, **kwargs)
            else:
                pk = self._name, args, frozenset(kwargs.items())
                calls = story._ids[self._binding]

        if pk in calls.expected:
            result, exception = calls.expected[pk]
            if exception is None:
                return result
            else:
                raise exception
        elif story._proxy:
            record = not story._recurse_lock or story._recurse_lock.acquire(False)
            try:
                try:
                    result = self._wrapped(*args, **kwargs)
                except Exception as exc:
                    if record:
                        calls.unexpected[pk] = None, exc
                    raise
                else:
                    if record:
                        calls.unexpected[pk] = result, None
                    return result
            finally:
                if record and story._recurse_lock:
                    story._recurse_lock.release()
        else:
            raise AssertionError("Unexpected call to %s with args:%s kwargs:%s" % pk)

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


class EntanglingBase(object):

    def __enter__(self):
        self.__entanglement = weave(
            self._target,
            partial(self.FunctionWrapper, story=self),
            methods=ALL_METHODS,
        )
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()


class Story(EntanglingBase):
    """
    This a simple yet flexible tool that can do "capture-replay mocking" or "test doubles" [1]_. It leverages
    ``aspectlib``'s powerful :obj:`weaver <aspectlib.weave>`.

    The ``Story`` allows some testing patterns that are hard to do with other tools:

    * **Proxied mocks**: partially mock `objects` and `modules` so they are called normally if the request is unknown.
    * **Stubs**: completely mock `objects` and `modules`. Raise errors if the request is unknown.

    The ``Story`` works in two of transactions:

    *   **The story**: You describe what calls you want to mocked. Initially you don't need to write this. Example:

        ::

            >>> import mymod
            >>> with Story(mymod) as story:
            ...     mymod.func('some arg') == 'some result'
            ...     mymod.func('bad arg') ** ValueError("can't use this")

    *   **The replay**: You run the code uses the interfaces mocked in the `story`. The `replay` always starts from a
        `story` instance and it runs in two modes:

        *   **stub mode**: The default. Unexpected uses of the mocked interfaces raise errors. Example:

            ::

                >>> with story.replay():
                ...     assert mymod.func('some arg') == 'some result'
                ...     try:
                ...         mymod.func('bad arg')
                ...     except ValueError as exc:
                ...         print("Sucess: exception <%s> was raised." % exc) # test success
                ...     else:
                ...         raise AssertionError("The test expected MyException to be raised")
                Sucess: exception <can't use this> was raised.

            While in the **stub mode**, if you try to run ``mymod.function('unexpected arg')`` you will get an
            ``AssertionError`` as that call wasn't specified in the **story**. Example:

            ::

                >>> with story.replay():
                ...     mymod.func('unexpected arg')
                Traceback (most recent call last):
                  ...
                  File "...aspectlib...test.py", line ..., in __call__
                    raise AssertionError("Unexpected call to %s with args:%s kwargs:%s" % pk)
                AssertionError: Unexpected call to mymod.func with args:('unexpected arg',) kwargs:frozenset(...)

        *   `proxy mode`: Unexpected uses are allowed but they are collected for later inspection. Example:

            ::

                >>> with story.replay(proxy=True) as replay:
                ...     assert mymod.func('some arg') == 'some result'
                ...     try:
                ...         mymod.func('bad arg')
                ...     except ValueError as exc:
                ...         print("Sucess: exception <%s> was raised." % exc) # test success
                ...     else:
                ...         raise AssertionError("The test expected MyException to be raised")
                ...     mymod.func('unexpected arg')
                Sucess: exception <can't use this> was raised.
                Got unexpected arg in the real code !


    One way to use this on existing code where it's not clear what needs to be written in the **story** is to start with
    an empty **story**, run the test code, check the unexpected usage and write the story from that. Example:

    ::

        >>> print(replay.missing())
        ### UNEXPECTED CALLS (add these in your story)
        <BLANKLINE>
        mymod.func('unexpected arg') == None  # returned
        <BLANKLINE>

    Now you can just copy that in your story.

    :param target: Targets to weave in the `story`/`replay` transactions.
    :type target: Same as for :obj:`aspectlib.weave`.

    .. versionchanged:: 0.9.0

        Added in.

    .. [1] http://www.martinfowler.com/bliki/TestDouble.html
    """
    FunctionWrapper = StoryFunctionWrapper

    def __init__(self, target):
        self._target = target
        self.calls = {}  # if calls is None else calls
        self._ids = {}

    def replay(self, **options):
        """
        :param bool proxy: If ``True`` the `replay` will work in `proxy mode`. Default: ``False`` (`stub mode`).
        :returns: A :obj:`aspectlib.test.Replay` object.
        """
        return Replay(self._target, self.calls, **options)

ReplayPair = namedtuple("ReplayPair", ('expected', 'unexpected'))


def _output_signature(out, name, args, kwargs, *resp):

    out.write('%s(%s%s%s)' % (
        name,
        ', '.join(repr(i) for i in args),
        ', ' if kwargs else '',
        ', '.join("%s=%r" % i for i in (kwargs.items() if isinstance(kwargs, dict) else kwargs)),
    ))
    if resp:
        result, exception = resp
        if exception is None:
            out.write(' == %s  # returned\n' % repr(result))
        else:
            out.write(' ** %s(%s)  # raised\n' % (qualname(type(exception)), ', '.join(repr(i) for i in args)))


def format_calls(calls, prefix=""):
    if calls:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", "comparing unequal types not supported", DeprecationWarning)
            out = StringIO()
            out.write("### %s\n\n" % prefix)
            instances = defaultdict(int)
            for pk in sorted(calls, key=repr):
                name, args, kwargs = pk
                resp = calls[pk]
                if isinstance(resp, tuple):
                    _output_signature(out, name, args, kwargs, *resp)
                else:
                    instance_name = camelcase_to_underscores(name.rsplit('.', 1)[-1])
                    instances[instance_name] += 1
                    instance_name = "%s_%s" % (instance_name, instances[instance_name])
                    out.write('%s = ' % instance_name)
                    _output_signature(out, name, args, kwargs)
                    if isinstance(resp, unexpected):
                        out.write('  # was never called in the Story !')
                    out.write('\n')
                    for pk in sorted(resp, key=repr):
                        name, args, kwargs = pk
                        iresp = resp[pk]
                        out.write('%s.' % instance_name)
                        _output_signature(out, name, args, kwargs, *iresp)
            return out.getvalue()
    else:
        return ""


class Replay(EntanglingBase):
    """
    Object implementing the `replay transaction`.

    This object should be created by :obj:`Story <aspectlib.test.Story>`'s :obj:`replay <aspectlib.test.Story.replay>`
    method.

    """
    FunctionWrapper = ReplayFunctionWrapper

    def __init__(self, target, expected, proxy=False, recurse_lock_factory=allocate_lock):
        self._target = target
        self.calls = ReplayPair(expected, {})
        self._ids = {}
        self._proxy = proxy
        self._recurse_lock = recurse_lock_factory()

    def missing(self, prefix=True):
        """
        Returns a pretty text representation of the unexpected calls (while the `replay` was run in `proxy mode`).
        """
        return format_calls(self.calls.unexpected, 'UNEXPECTED CALLS (add these in your story)' if prefix else '')
