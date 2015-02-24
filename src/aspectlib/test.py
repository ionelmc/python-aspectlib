from collections import defaultdict
from collections import namedtuple
from difflib import unified_diff
from functools import partial
from functools import wraps
from inspect import isclass
from logging import getLevelName
from logging import getLogger
from sys import _getframe
from traceback import format_stack

from aspectlib import ALL_METHODS
from aspectlib import mimic
from aspectlib import weave

from .utils import camelcase_to_underscores
from .utils import container
from .utils import logf
from .utils import qualname
from .utils import repr_ex
from .utils import Sentinel

try:
    from logging import _levelNames as nameToLevel
except ImportError:
    from logging import _nameToLevel as nameToLevel
try:
    from dummy_thread import allocate_lock
except ImportError:
    from _dummy_thread import allocate_lock
try:
    from collections import OrderedDict
except ImportError:
    from .py2ordereddict import OrderedDict
try:
    from collections import ChainMap
except ImportError:
    from .py2chainmap import ChainMap

__all__ = 'mock', 'record', "Story"

logger = getLogger(__name__)
logexception = logf(logger.exception)

Call = namedtuple('Call', ('self', 'args', 'kwargs'))
CallEx = namedtuple('CallEx', ('self', 'name', 'args', 'kwargs'))
Result = namedtuple('Result', ('self', 'args', 'kwargs', 'result', 'exception'))
ResultEx = namedtuple('ResultEx', ('self', 'name', 'args', 'kwargs', 'result', 'exception'))
_INIT = Sentinel("INIT")


def mock(return_value, call=False):
    """
    Factory for a decorator that makes the function return a given `return_value`.

    Args:
        return_value: Value to return from the wrapper.
        call (bool): If ``True``, call the decorated function. (default: ``False``)

    Returns:
        A decorator.
    """

    def mock_decorator(func):
        @wraps(func)
        def mock_wrapper(*args, **kwargs):
            if call:
                func(*args, **kwargs)
            return return_value

        return mock_wrapper

    return mock_decorator


class LogCapture(object):
    """
    Records all log messages made on the given logger. Assumes the logger has a ``_log`` method.

    Example::

        >>> import logging
        >>> logger = logging.getLogger('mylogger')
        >>> with LogCapture(logger, level='INFO') as logs:
        ...     logger.debug("Message from debug: %s", 'somearg')
        ...     logger.info("Message from info: %s", 'somearg')
        ...     logger.error("Message from error: %s", 'somearg')
        >>> logs.calls
        [('Message from info: %s', ('somearg',), 'INFO'), ('Message from error: %s', ('somearg',), 'ERROR')]
        >>> logs.messages
        [('INFO', 'Message from info: somearg'), ('ERROR', 'Message from error: somearg')]
        >>> logs.has('Message from info: %s')
        True
        >>> logs.has('Message from info: somearg')
        True
        >>> logs.has('Message from info: %s', 'badarg')
        False
        >>> logs.has('Message from debug: %s')
        False
        >>> logs.assertLogged('Message from error: %s')
        >>> logs.assertLogged('Message from error: %s')
        >>> logs.assertLogged('Message from error: %s')

    .. versionchanged:: 1.3.0

        Added ``messages`` property.
        Changed ``calls`` to retrun the level as a string (instead of int).
    """
    def __init__(self, logger, level='DEBUG'):
        self._logger = logger
        self._level = nameToLevel[level]
        self._calls = []
        self._rollback = None

    def __enter__(self):
        self._rollback = weave(
            self._logger,
            record(callback=self._callback, extended=True, iscalled=True),
            methods='_log$'
        )
        return self

    def __exit__(self, *exc):
        self._rollback()

    def _callback(self, _binding, _qualname, args, _kwargs):
        level, message, args = args
        if level >= self._level:
            self._calls.append((
                message % args if args else message,
                message,
                args,
                getLevelName(level)
            ))

    @property
    def calls(self):
        return [i[1:] for i in self._calls]

    @property
    def messages(self):
        return [(i[-1], i[0]) for i in self._calls]

    def has(self, message, *args, **kwargs):
        level = kwargs.pop('level', None)
        assert not kwargs, "Unexpected arguments: %s" % kwargs
        for call_final_message, call_message, call_args, call_level in self._calls:
            if level is None or level == call_level:
                if (
                    message == call_message and args == call_args
                    if args else
                    message == call_final_message or message == call_message
                ):
                    return True
        return False

    def assertLogged(self, message, *args, **kwargs):
        if not self.has(message, *args, **kwargs):
            raise AssertionError("There's no such message %r (with args %r) logged on %s. Logged messages where: %s" % (
                message, args, self._logger, self.calls
            ))


class _RecordingFunctionWrapper(object):
    """
    Function wrapper that records calls and can be used as an weaver context manager.

    See :obj:`aspectlib.test.record` for arguments.
    """

    def __init__(self, wrapped, iscalled=True, calls=None, callback=None, extended=False, results=False,
                 recurse_lock=None, binding=None):
        assert not results or iscalled, "`iscalled` must be True if `results` is True"
        mimic(self, wrapped)
        self.__wrapped = wrapped
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
            self.__callback(self.__binding, qualname(self), args, kwargs, *response)
        if self.calls is not None:
            if self.__extended:
                self.calls.append((ResultEx if response else CallEx)(
                    self.__binding, qualname(self), args, kwargs, *response
                ))
            else:
                self.calls.append((Result if response else Call)(
                    self.__binding, args, kwargs, *response
                ))

    def __get__(self, instance, owner):
        return _RecordingFunctionWrapper(
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

    Args:
        callback (list):
            An a callable that is to be called with ``instance, function, args, kwargs``.
        calls (list):
            An object where the `Call` objects are appended. If not given and ``callback`` is not specified then a new list
            object will be created.
        iscalled (bool):
            If ``True`` the `func` will be called. (default: ``False``)
        extended (bool):
            If ``True`` the `func`'s ``__name__`` will also be included in the call list. (default: ``False``)
        results (bool):
            If ``True`` the results (and exceptions) will also be included in the call list. (default: ``False``)

    Returns:
        A wrapper that records all calls made to `func`. The history is available as a ``call``
        property. If access to the function is too hard then you need to specify the history manually.

    Example:

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
        return _RecordingFunctionWrapper(
            func,
            recurse_lock=recurse_lock_factory(),
            **options
        )
    else:
        return partial(record, **options)


class StoryResultWrapper(object):
    __slots__ = '__recorder__'

    def __init__(self, recorder):
        self.__recorder__ = recorder

    def __eq__(self, result):
        self.__recorder__(_Returns(result))

    def __pow__(self, exception):
        if not (isinstance(exception, BaseException) or isclass(exception) and issubclass(exception, BaseException)):
            raise RuntimeError("Value %r must be an exception type or instance." % exception)
        self.__recorder__(_Raises(exception))

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
        exec("%s = __unsupported__" % mm)


class _StoryFunctionWrapper(object):
    def __init__(self, wrapped, handle, binding=None, owner=None):
        self._wrapped = wrapped
        self._name = wrapped.__name__
        self._handle = handle
        self._binding = binding
        self._owner = owner

    @property
    def _qualname(self):
        return qualname(self)

    def __call__(self, *args, **kwargs):
        if self._binding is None:
            return StoryResultWrapper(partial(self._handle, None, self._qualname, args, kwargs))
        else:
            if self._name == '__init__':
                self._handle(None, qualname(self._owner), args, kwargs, _Binds(self._binding))
            else:
                return StoryResultWrapper(partial(self._handle, self._binding, self._name, args, kwargs))

    def __get__(self, binding, owner):
        return mimic(type(self)(
            self._wrapped.__get__(binding, owner) if hasattr(self._wrapped, '__get__') else self._wrapped,
            handle=self._handle,
            binding=binding,
            owner=owner,
        ), self)


class _ReplayFunctionWrapper(_StoryFunctionWrapper):
    def __call__(self, *args, **kwargs):
        if self._binding is None:
            return self._handle(None, self._qualname, args, kwargs, self._wrapped)
        else:
            if self._name == '__init__':
                self._handle(None, qualname(self._owner), args, kwargs, self._wrapped, _Binds(self._binding))
            else:
                return self._handle(self._binding, self._name, args, kwargs, self._wrapped)


class _RecordingBase(object):
    _target = None
    _options = None

    def __init__(self, target, **options):
        self._target = target
        self._options = options
        self._calls = OrderedDict()
        self._ids = {}
        self._instances = defaultdict(int)

    def _make_key(self, binding, name, args, kwargs):
        if binding is not None:
            binding, _ = self._ids[id(binding)]
        return (
            binding,
            name,
            ', '.join(repr_ex(i) for i in args),
            ', '.join("%s=%s" % (k, repr_ex(v)) for k, v in kwargs.items())
        )

    def _tag_result(self, name, result):
        if isinstance(result, _Binds):
            instance_name = camelcase_to_underscores(name.rsplit('.', 1)[-1])
            self._instances[instance_name] += 1
            instance_name = "%s_%s" % (instance_name, self._instances[instance_name])
            self._ids[id(result.value)] = instance_name, result.value
            result.value = instance_name
        else:
            result.value = repr_ex(result.value, self._ids)
        return result

    def _handle(self, binding, name, args, kwargs, result):
        pk = self._make_key(binding, name, args, kwargs)
        result = self._tag_result(name, result)
        assert pk not in self._calls or self._calls[pk] == result, (
            "Story creation inconsistency. There is already a result cached for "
            "binding:%r name:%r args:%r kwargs:%r and it's: %r." % (
                binding, name, args, kwargs, self._calls[pk]
            )
        )
        self._calls[pk] = result

    def __enter__(self):
        self._options.setdefault('methods', ALL_METHODS)
        self.__entanglement = weave(
            self._target,
            partial(self._FunctionWrapper, handle=self._handle),
            **self._options
        )
        return self

    def __exit__(self, *args):
        self.__entanglement.rollback()
        del self._ids


_Raises = container("Raises")
_Returns = container("Returns")
_Binds = container("Binds")


class Story(_RecordingBase):
    """
        This a simple yet flexible tool that can do "capture-replay mocking" or "test doubles" [1]_. It leverages
        ``aspectlib``'s powerful :obj:`weaver <aspectlib.weave>`.

        Args:
            target (same as for :obj:`aspectlib.weave`):
                Targets to weave in the `story`/`replay` transactions.
            subclasses (bool):
                If ``True``, subclasses of target are weaved. *Only available for classes*
            aliases (bool):
                If ``True``, aliases of target are replaced.
            lazy (bool):
                If ``True`` only target's ``__init__`` method is patched, the rest of the methods are patched after ``__init__``
                is called. *Only available for classes*.
            methods (list or regex or string): Methods from target to patch. *Only available for classes*

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
    _FunctionWrapper = _StoryFunctionWrapper

    def __init__(self, *args, **kwargs):
        super(Story, self).__init__(*args, **kwargs)
        frame = _getframe(1)
        self._context = frame.f_globals, frame.f_locals

    def replay(self, **options):
        """
        Args:
            proxy (bool):
                If ``True`` then unexpected uses are allowed (will use the real functions) but they are collected for later
                use. Default: ``True``.
            strict (bool):
                If ``True`` then an ``AssertionError`` is raised when there were `unexpected calls` or there were `missing
                calls` (specified in the story but not called). Default: ``True``.
            dump (bool):
                If ``True`` then the `unexpected`/`missing calls` will be printed (to ``sys.stdout``). Default: ``True``.

        Returns:
            A :obj:`aspectlib.test.Replay` object.

        Example:

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
                 mymod.func('some arg') == 'some result'  # returns
                -mymod.func('other arg') == 'other result'  # returns
                +mymod.func('bogus arg') == None  # returns
            ACTUAL:
                mymod.func('some arg') == 'some result'  # returns
                mymod.func('bogus arg') == None  # returns
            <BLANKLINE>
        """
        options.update(self._options)
        return Replay(self, **options)

ReplayPair = namedtuple("ReplayPair", ('expected', 'actual'))


def logged_eval(value, context):
    try:
        return eval(value, *context)
    except:
        logexception("Failed to evaluate %r.\nContext:\n%s", value, ''.join(format_stack(
            f=_getframe(1),
            limit=15
        )))
        raise


class Replay(_RecordingBase):
    """
    Object implementing the `replay transaction`.

    This object should be created by :obj:`Story <aspectlib.test.Story>`'s :obj:`replay <aspectlib.test.Story.replay>`
    method.
    """
    _FunctionWrapper = _ReplayFunctionWrapper

    def __init__(self, play, proxy=True, strict=True, dump=True, recurse_lock=False, **options):
        super(Replay, self).__init__(play._target, **options)
        self._calls, self._expected, self._actual = ChainMap(self._calls, play._calls), play._calls, self._calls

        self._proxy = proxy
        self._strict = strict
        self._dump = dump
        self._context = play._context
        self._recurse_lock = allocate_lock() if recurse_lock is True else (recurse_lock and recurse_lock())

    def _handle(self, binding, name, args, kwargs, wrapped, bind=None):
        pk = self._make_key(binding, name, args, kwargs)
        if pk in self._expected:
            result = self._actual[pk] = self._expected[pk]
            if isinstance(result, _Binds):
                self._tag_result(name, bind)
            elif isinstance(result, _Returns):
                return logged_eval(result.value, self._context)
            elif isinstance(result, _Raises):
                raise logged_eval(result.value, self._context)
            else:
                raise RuntimeError('Internal failure - unknown result: %r' % result)  # pragma: no cover
        else:
            if self._proxy:
                shouldrecord = not self._recurse_lock or self._recurse_lock.acquire(False)
                try:
                    try:
                        if bind:
                            bind = self._tag_result(name, bind)
                        result = wrapped(*args, **kwargs)
                    except Exception as exc:
                        if shouldrecord:
                            self._calls[pk] = self._tag_result(name, _Raises(exc))
                        raise
                    else:
                        if shouldrecord:
                            self._calls[pk] = bind or self._tag_result(name, _Returns(result))
                        return result
                finally:
                    if shouldrecord and self._recurse_lock:
                        self._recurse_lock.release()
            else:
                raise AssertionError("Unexpected call to %s/%s with args:%s kwargs:%s" % pk)

    def _unexpected(self, _missing=False):
        if _missing:
            expected, actual = self._actual, self._expected
        else:
            actual, expected = self._actual, self._expected
        return ''.join(_format_calls(OrderedDict(
            (pk, val) for pk, val in actual.items()
            if pk not in expected or val != expected.get(pk)
        )))

    @property
    def unexpected(self):
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
            >>> print(replay.unexpected)
            mymod.func('some arg') == None  # returns
            mymod.badfunc() ** ValueError('boom!',)  # raises
            <BLANKLINE>

        We can just take the output and paste in the story::

            >>> import mymod
            >>> with Story(mymod) as story:
            ...     mymod.func('some arg') == None  # returns
            ...     mymod.badfunc() ** ValueError('boom!')  # raises
            >>> with story.replay():
            ...     mymod.func('some arg')
            ...     try:
            ...         mymod.badfunc()
            ...     except ValueError as exc:
            ...         print(exc)
            boom!

        """
        return self._unexpected()

    @property
    def missing(self):
        """
        Returns a pretty text representation of just the missing calls.
        """
        return self._unexpected(_missing=True)

    @property
    def diff(self):
        """
        Returns a pretty text representation of the unexpected and missing calls.

        Most of the time you don't need to directly use this. This is useful when you run the `replay` in
        ``strict=False`` mode and want to do custom assertions.

        """
        actual = list(_format_calls(self._actual))
        expected = list(_format_calls(self._expected))
        return ''.join(unified_diff(expected, actual, fromfile='expected', tofile='actual'))

    @property
    def actual(self):
        return ''.join(_format_calls(self._actual))

    @property
    def expected(self):
        return ''.join(_format_calls(self._expected))

    def __exit__(self, *exception):
        super(Replay, self).__exit__()
        if self._strict or self._dump:
            diff = self.diff
            if diff:
                if exception or self._dump:
                    print('STORY/REPLAY DIFF:')
                    print('    ' + '\n    '.join(diff.splitlines()))
                    print('ACTUAL:')
                    print('    ' + '    '.join(_format_calls(self._actual)))
                if not exception and self._strict:
                    raise AssertionError(diff)


def _format_calls(calls):
    for (binding, name, args, kwargs), result in calls.items():
        sig = '%s(%s%s%s)' % (name, args, ', ' if kwargs and args else '', kwargs)

        if isinstance(result, _Binds):
            yield '%s = %s\n' % (result.value, sig)
        elif isinstance(result, _Returns):
            if binding is None:
                yield '%s == %s  # returns\n' % (sig, result.value)
            else:
                yield '%s.%s == %s  # returns\n' % (binding, sig, result.value)
        elif isinstance(result, _Raises):
            if binding is None:
                yield '%s ** %s  # raises\n' % (sig, result.value)
            else:
                yield '%s.%s ** %s  # raises\n' % (binding, sig, result.value)
