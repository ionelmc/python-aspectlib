import logging
import os
import sys
from itertools import islice
import string

from wrapt import decorator

logger = logging.getLogger(__name__)


def frame_iterator(frame):
    while frame:
        yield frame
        frame = frame.f_back


def format_stack(skip=0, length=6, _sep=os.path.sep):
    return ' < '.join("%s:%s:%s" % (
        '/'.join(f.f_code.co_filename.split(_sep)[-2:]),
        f.f_lineno,
        f.f_code.co_name
    ) for f in islice(frame_iterator(sys._getframe(1 + skip)), length))

ASCII_ONLY = ''.join(i if i in string.printable else '.' for i in (chr(c) for c in range(256)))


def strip_non_ascii(val):
    return str(val).translate(ASCII_ONLY)


def log(func=None,
        stacktrace=10,
        stacktrace_align=60,
        attributes=(),
        module=True,
        arguments=True,
        arguments_repr=repr,
        result=True,
        exception=True,
        exception_repr=repr,
        result_repr=strip_non_ascii,
        use_logging='CRITICAL',
        print_to=None):
    loglevel = use_logging and logging._levelNames.get(use_logging, logging.CRITICAL)

    def dump(buf):
        try:
            if use_logging:
                logger._log(loglevel, buf, ())
            if print_to:
                buf += '\n'
                print_to.write(buf)
        except Exception as exc:
            logger.critical('Failed to log a message: %s', exc, exc_info=True)

    @decorator
    def logged(func, instance, args, kwargs, _missing=object()):
        name = func.__name__
        if instance:
            instance_type = type(instance)
            info = []
            for key in attributes:
                if key.endswith('()'):
                    call = key = key.rstrip('()')
                else:
                    call = False
                val = getattr(instance, key, _missing)
                if val is not _missing and key != name:
                    info.append(' %s=%s' % (
                        key, arguments_repr(val() if call else val)
                    ))
            sig = buf = '{%s%s%s}.%s' % (
                instance_type.__module__ + '.' if module else '',
                instance_type.__name__,
                ''.join(info),
                name
            )
        else:
            sig = buf = func.__name__
        if arguments:
            buf += '(%s%s)' % (
                ', '.join(repr(i) for i in (args if arguments is True else args[:arguments])),
                ((', ' if args else '') + ', '.join('%s=%r' % i for i in kwargs.items()))
                if kwargs and arguments is True
                else '',
            )
        if stacktrace:
            buf = ("%%-%ds  <<< %%s" % stacktrace_align) % (buf, format_stack(skip=1, length=stacktrace))
        dump(buf)
        try:
            res = func(*args, **kwargs)
        except Exception as exc:
            if exception:
                dump('%s ~ raised %s' % (sig, exception_repr(exc)))
            raise

        if result:
            dump('%s => %s' % (sig, result_repr(res)))
        return res

    if func:
        return logged(func)
    else:
        return logged
