from collections import defaultdict
from collections import namedtuple
from functools import partial
from functools import wraps
from inspect import isclass
from difflib import unified_diff

from aspectlib import ALL_METHODS
from aspectlib import mimic
from aspectlib import weave

from .utils import camelcase_to_underscores
from .utils import make_signature
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
        self.__binding = binding
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
            self.__callback(self.__binding, self.__name, args, kwargs, *response)
        if self.calls is not None:
            if self.__extended:
                self.calls.append((ResultEx if response else CallEx)(
                    self.__binding, self.__name, args, kwargs, *response
                ))
            else:
                self.calls.append((Result if response else Call)(
                    self.__binding, args, kwargs, *response
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
        self._story = story
        self._binding = binding
        self._owner = owner

    @property
    def _qualname(self):
        return qualname(self)

    def __call__(self, *args, **kwargs):
        story = self._story
        if self._binding is None:
            pk = self._qualname, args, frozenset(kwargs.items())
            return StoryResultWrapper(partial(self._save, story._calls, pk))
        else:
            if self._name == '__init__':
                pk = qualname(self._owner), args, frozenset(kwargs.items())
                story._ids[self._binding] = self._save(story._calls, pk, {})
            else:
                pk = self._name, args, frozenset(kwargs.items())
                return StoryResultWrapper(partial(self._save, story._ids[self._binding], pk))

    def _save(self, calls, pk, response):
        assert pk not in calls, "Story creation inconsistency. There is already a call cache for %r and it's: %r." % (pk, calls[pk])
        calls[pk] = response
        return response

    def __get__(self, binding, owner):
        return mimic(type(self)(
            self._wrapped.__get__(binding, owner),
            story=self._story,
            binding=binding,
            owner=owner,
        ), self)


class Unexpected(dict):
    def __repr__(self):
        return "Unexpected(%s)" % super(Unexpected, self).__repr__()


class ReplayFunctionWrapper(StoryFunctionWrapper):
    def __call__(self, *args, **kwargs):
        story = self._story
        if self._binding is None:
            pk = self._qualname, args, frozenset(kwargs.items())
            calls = story._calls
        else:
            if self._name == '__init__':
                pk = qualname(self._owner), args, frozenset(kwargs.items())
                calls = story._calls
                if pk in calls.expected:
                    story._ids[self._binding] = ReplayPair(calls.expected[pk], calls.actual.setdefault(pk, {}))
                    return
                elif story._proxy:
                    story._ids[self._binding] = ReplayPair({}, calls.actual.setdefault(pk, Unexpected()))
                    return self._wrapped(*args, **kwargs)
            else:
                pk = self._name, args, frozenset(kwargs.items())
                calls = story._ids[self._binding]

        if pk in calls.expected:
            result, exception = calls.actual[pk] = calls.expected[pk]
            if exception is None:
                return result
            else:
                raise exception() if isclass(exception) else exception
        elif story._proxy:
            record = not story._recurse_lock or story._recurse_lock.acquire(False)
            try:
                try:
                    result = self._wrapped(*args, **kwargs)
                except Exception as exc:
                    if record:
                        calls.actual[pk] = None, exc
                    raise
                else:
                    if record:
                        calls.actual[pk] = result, None
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
    _target = None
    _options = None

    def __enter__(self):
        self._options.setdefault('methods', ALL_METHODS)

        self.__entanglement = weave(
            self._target,
            partial(self.FunctionWrapper, story=self),
            **self._options
        )
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()


class Story(EntanglingBase):
    """
    This a simple yet flexible tool that can do "capture-replay mocking" or "test doubles" [1]_. It leverages
    ``aspectlib``'s powerful :obj:`weaver <aspectlib.weave>`.

    :param target:
        Targets to weave in the `story`/`replay` transactions.
    :type target:
        Same as for :obj:`aspectlib.weave`.
    :param bool subclasses:
        If ``True``, subclasses of target are weaved. *Only available for classes*
    :param bool aliases:
        If ``True``, aliases of target are replaced.
    :param bool lazy:
        If ``True`` only target's ``__init__`` method is patched, the rest of the methods are patched after ``__init__``
        is called. *Only available for classes*.
    :param methods: Methods from target to patch. *Only available for classes*
    :type methods: list or regex or string

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

    *   **The replay**: You run the code uses the interfaces mocked in the `story`. The :obj:`replay
        <aspectlib.test.Story.replay>` always starts from a `story` instance.

    .. versionchanged:: 0.9.0

        Added in.

    .. [1] http://www.martinfowler.com/bliki/TestDouble.html
    """
    FunctionWrapper = StoryFunctionWrapper

    def __init__(self, target, **options):
        self._target = target
        self._options = options
        self._calls = {}  # if calls is None else calls
        self._ids = {}

    def replay(self, **options):
        """
        :param bool proxy:
            If ``True`` then unexpected uses are allowed (will use the real functions) but they are collected for later
            use. Default: ``True``.
        :param bool strict:
            If ``True`` then an ``AssertionError`` is raised when there were `unexpected calls` or there were `missing
            calls` (specified in the story but not called). Default: ``True``.
        :param bool dump:
            If ``True`` then the `unexpected`/`missing calls` will be printed (to ``sys.stdout``). Default: ``True``.
        :returns: A :obj:`aspectlib.test.Replay` object.

        Example::

            >>> import mymod
            >>> with Story(mymod) as story:
            ...     mymod.func('some arg') == 'some result'
            ...     mymod.func('other arg') == 'other result'
            >>> with story.replay(strict=False):
            ...     print(mymod.func('some arg'))
            ...     mymod.func('bogus arg')
            some result
            Got bogus arg in the real code !
            STORY/REPLAY DIFF:
                --- expected...
                +++ actual...
                @@ -1,2 +1,2 @@
                -mymod.func('other arg') == 'other result'  # returns
                +mymod.func('bogus arg') == None  # returns
                 mymod.func('some arg') == 'some result'  # returns

        """
        options.update(self._options)
        return Replay(self._target, self._calls, **options)

ReplayPair = namedtuple("ReplayPair", ('expected', 'actual'))


class Replay(EntanglingBase):
    """
    Object implementing the `replay transaction`.

    This object should be created by :obj:`Story <aspectlib.test.Story>`'s :obj:`replay <aspectlib.test.Story.replay>`
    method.
    """
    FunctionWrapper = ReplayFunctionWrapper

    def __init__(self, target, expected, proxy=True, strict=True, dump=True, recurse_lock_factory=allocate_lock, **options):
        self._target = target
        self._options = options
        self._calls = ReplayPair(expected, {})
        self._ids = {}
        self._proxy = proxy
        self._strict = strict
        self._dump = dump
        self._recurse_lock = recurse_lock_factory()

    def unexpected(self, _missing=False):
        """
        Returns a pretty text representation of just the unexpected calls.

        The output should be usable directly in the story (just copy-paste it). Example::

            >>> import mymod
            >>> with Story(mymod) as story:
            ...     pass
            >>> with story.replay(strict=False, dump=False) as replay:
            ...     mymod.func('some arg')
            ...     try:
            ...         mymod.badfunc()
            ...     except ValueError as exc:
            ...         print(exc)
            Got some arg in the real code !
            boom!
            >>> print(replay.unexpected())
            mymod.badfunc() ** ValueError('boom!')  # raises
            mymod.func('some arg') == None  # returns
            <BLANKLINE>

        We can just take the output and paste in the story::

            >>> import mymod
            >>> with Story(mymod) as story:
            ...     mymod.badfunc() ** ValueError('boom!')  # raises
            ...     mymod.func('some arg') == None  # returns
            >>> with story.replay():
            ...     mymod.func('some arg')
            ...     try:
            ...         mymod.badfunc()
            ...     except ValueError as exc:
            ...         print(exc)
            boom!

        """
        unexpected = {}
        if _missing:
            expected, actual = self._calls.actual, self._calls.expected
        else:
            actual, expected = self._calls.actual, self._calls.expected

        for pk, val in actual.items():
            expected_val = expected.get(pk, None)
            if pk not in expected or val != expected_val:
                if isinstance(val, tuple):
                    unexpected[pk] = val
                elif expected_val is None:
                    unexpected[pk] = Unexpected(val)
                else:
                    iunexpected = unexpected[pk] = {}
                    for pk, val in val.items():
                        if pk not in expected_val:
                            iunexpected[pk] = val
        return format_calls(unexpected)

    def missing(self):
        """
        Returns a pretty text representation of just the missing calls.
        """
        return self.unexpected(_missing=True)

    def diff(self):
        """
        Returns a pretty text representation of the unexpected and missing calls.

        Most of the time you don't need to directly use this. This is useful when you run the `replay` in
        ``strict=False`` mode and want to do custom assertions.

        """
        actual = format_calls(self._calls.actual).splitlines(True)
        expected = format_calls(self._calls.expected).splitlines(True)
        return ''.join(unified_diff(expected, actual, fromfile='expected', tofile='actual'))

    def __exit__(self, *args):
        super(Replay, self).__exit__()
        if self._strict or self._dump:
            diff = self.diff()
            if diff:
                if self._dump:
                    print('STORY/REPLAY DIFF:')
                    print('    ' + '\n    '.join(diff.splitlines()))
                if self._strict:
                    raise AssertionError(diff)


def format_calls(calls):
    if calls:
        out = StringIO()
        instances = defaultdict(int)
        for pk in sorted(calls, key=repr):
            name, args, kwargs = pk
            resp = calls[pk]
            if isinstance(resp, tuple):
                out.write(make_signature(name, args, kwargs, *resp))
            else:
                instance_name = camelcase_to_underscores(name.rsplit('.', 1)[-1])
                instances[instance_name] += 1
                instance_name = "%s_%s" % (instance_name, instances[instance_name])
                out.write('%s = %s' % (instance_name, make_signature(name, args, kwargs)))
                if isinstance(resp, Unexpected):
                    out.write('  # was never called !')
                out.write('\n')
                for pk in sorted(resp, key=repr):
                    name, args, kwargs = pk
                    iresp = resp[pk]
                    out.write('%s.%s' % (instance_name, make_signature(name, args, kwargs, *iresp)))
        return out.getvalue()
    else:
        return ""
