import logging
import os
import string
import sys
from itertools import islice

from aspectlib import Aspect
from aspectlib import mimic

try:
    from types import InstanceType
except ImportError:
    InstanceType = type(None)

logger = logging.getLogger(__name__)


def frame_iterator(frame):
    """
    Yields frames till there are no more.
    """
    while frame:
        yield frame
        frame = frame.f_back


def format_stack(skip=0, length=6, _sep=os.path.sep):
    """
    Returns a one-line string with the current callstack.
    """
    return ' < '.join("%s:%s:%s" % (
        '/'.join(f.f_code.co_filename.split(_sep)[-2:]),
        f.f_lineno,
        f.f_code.co_name
    ) for f in islice(frame_iterator(sys._getframe(1 + skip)), length))

PRINTABLE = string.digits + string.ascii_letters + string.punctuation + ' '
ASCII_ONLY = ''.join(i if i in PRINTABLE else '.' for i in (chr(c) for c in range(256)))


def strip_non_ascii(val):
    """
    Convert to string (using `str`) and replace non-ascii characters with a dot (``.``).
    """
    return str(val).translate(ASCII_ONLY)


def log(func=None,
        stacktrace=10,
        stacktrace_align=60,
        attributes=(),
        module=True,
        call=True,
        call_args=True,
        call_args_repr=repr,
        result=True,
        exception=True,
        exception_repr=repr,
        result_repr=strip_non_ascii,
        use_logging='CRITICAL',
        print_to=None):
    """
    Decorates `func` to have logging.

    Args
        func (function):
            Function to decorate. If missing log returns a partial which you can use as a decorator.
        stacktrace (int):
            Number of frames to show.
        stacktrace_align (int):
            Column to align the framelist to.
        attributes (list):
            List of instance attributes to show, in case the function is a instance method.
        module (bool):
            Show the module.
        call (bool):
            If ``True``, then show calls. If ``False`` only show the call details on exceptions (if ``exception`` is
            enabled) (default: ``True``)
        call_args (bool):
            If ``True``, then show call arguments. (default: ``True``)
        call_args_repr (bool):
            Function to convert one argument to a string. (default: ``repr``)
        result (bool):
            If ``True``, then show result. (default: ``True``)
        exception (bool):
            If ``True``, then show exceptions. (default: ``True``)
        exception_repr (function):
            Function to convert an exception to a string. (default: ``repr``)
        result_repr (function):
            Function to convert the result object to a string. (default: ``strip_non_ascii`` - like ``str`` but nonascii
            characters are replaced with dots.)
        use_logging (string):
            Emit log messages with the given loglevel. (default: ``"CRITICAL"``)
        print_to (fileobject):
            File object to write to, in case you don't want to use logging module. (default: ``None`` - printing is
            disabled)

    Returns:
        A decorator or a wrapper.

    Example:

        >>> @log(print_to=sys.stdout)
        ... def a(weird=False):
        ...     if weird:
        ...         raise RuntimeError('BOOM!')
        >>> a()
        a()                                                           <<< ...
        a => None
        >>> try:
        ...     a(weird=True)
        ... except Exception:
        ...     pass # naughty code !
        a(weird=True)                                                 <<< ...
        a ~ raised RuntimeError('BOOM!',)

    You can conveniently use this to logs just errors, or just results, example::

        >>> import aspectlib
        >>> with aspectlib.weave(float, log(call=False, result=False, print_to=sys.stdout)):
        ...     try:
        ...         float('invalid')
        ...     except Exception as e:
        ...         pass # naughty code !
        float('invalid')                                              <<< ...
        float ~ raised ValueError(...float...invalid...)

    This makes debugging naughty code easier.

    PS: Without the weaving it looks like this::

        >>> try:
        ...     log(call=False, result=False, print_to=sys.stdout)(float)('invalid')
        ... except Exception:
        ...     pass # naughty code !
        float('invalid')                                              <<< ...
        float ~ raised ValueError(...float...invalid...)


    .. versionchanged:: 0.5.0

        Renamed `arguments` to `call_args`.
        Renamed `arguments_repr` to `call_args_repr`.
        Added `call` option.
    """

    loglevel = use_logging and (
        logging._levelNames if hasattr(logging, '_levelNames') else logging._nameToLevel
    ).get(use_logging, logging.CRITICAL)
    _missing = object()

    def dump(buf):
        try:
            if use_logging:
                logger._log(loglevel, buf, ())
            if print_to:
                buf += '\n'
                print_to.write(buf)
        except Exception as exc:
            logger.critical('Failed to log a message: %s', exc, exc_info=True)

    class __logged__(Aspect):
        __slots__ = 'cutpoint_function', 'final_function', 'binding', '__name__', '__weakref__'

        bind = False

        def __init__(self, cutpoint_function, binding=None):
            mimic(self, cutpoint_function)
            self.cutpoint_function = cutpoint_function
            self.final_function = super(__logged__, self).__call__(cutpoint_function)
            self.binding = binding

        def __get__(self, instance, owner):
            return __logged__(self.cutpoint_function.__get__(instance, owner), instance)

        def __call__(self, *args, **kwargs):
            return self.final_function(*args, **kwargs)

        def advising_function(self, *args, **kwargs):
            name = self.cutpoint_function.__name__
            instance = self.binding
            if instance is not None:
                if isinstance(instance, InstanceType):
                    instance_type = instance.__class__
                else:
                    instance_type = type(instance)

                info = []
                for key in attributes:
                    if key.endswith('()'):
                        callarg = key = key.rstrip('()')
                    else:
                        callarg = False
                    val = getattr(instance, key, _missing)
                    if val is not _missing and key != name:
                        info.append(' %s=%s' % (
                            key, call_args_repr(val() if callarg else val)
                        ))
                sig = buf = '{%s%s%s}.%s' % (
                    instance_type.__module__ + '.' if module else '',
                    instance_type.__name__,
                    ''.join(info),
                    name
                )
            else:
                sig = buf = name
            if call_args:
                buf += '(%s%s)' % (
                    ', '.join(repr(i) for i in (args if call_args is True else args[:call_args])),
                    ((', ' if args else '') + ', '.join('%s=%r' % i for i in kwargs.items()))
                    if kwargs and call_args is True
                    else '',
                )
            if stacktrace:
                buf = ("%%-%ds  <<< %%s" % stacktrace_align) % (buf, format_stack(skip=1, length=stacktrace))
            if call:
                dump(buf)
            try:
                res = yield
            except Exception as exc:
                if exception:
                    if not call:
                        dump(buf)
                    dump('%s ~ raised %s' % (sig, exception_repr(exc)))
                raise

            if result:
                dump('%s => %s' % (sig, result_repr(res)))

    if func:
        return __logged__(func)
    else:
        return __logged__
