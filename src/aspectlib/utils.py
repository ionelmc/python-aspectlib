from __future__ import print_function

import platform
import logging
import re
import os
import sys
from collections import deque
from functools import wraps
from inspect import isclass


RegexType = type(re.compile(""))

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PY26 = PY2 and sys.version_info[1] == 6
PYPY = platform.python_implementation() == 'PyPy'

if PY3:
    basestring = str
else:
    basestring = str, unicode  # flake8: noqa

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')

DEBUG = os.getenv('ASPECTLIB_DEBUG')


def logf(logger_func):
    @wraps(logger_func)
    def log_wrapper(*args):
        if DEBUG:
            logProcesses = logging.logProcesses
            logThreads = logging.logThreads
            logMultiprocessing = logging.logMultiprocessing
            logging.logThreads = logging.logProcesses = logMultiprocessing = False
            # disable logging pids and tids - we don't want extra calls around, especilly when we monkeypatch stuff
            try:
                return logger_func(*args)
            finally:
                logging.logProcesses = logProcesses
                logging.logThreads = logThreads
                logging.logMultiprocessing = logMultiprocessing
    return log_wrapper


def camelcase_to_underscores(name):
    s1 = FIRST_CAP_RE.sub(r'\1_\2', name)
    return ALL_CAP_RE.sub(r'\1_\2', s1).lower()


def qualname(obj):
    if hasattr(obj, '__module__') and obj.__module__ not in ('builtins', 'exceptions'):
        return '%s.%s' % (obj.__module__, obj.__name__)
    else:
        return obj.__name__


def force_bind(func):
    def bound(self, *args, **kwargs):  # pylint: disable=W0613
        return func(*args, **kwargs)
    bound.__name__ = func.__name__
    bound.__doc__ = func.__doc__
    return bound


def make_method_matcher(regex_or_regexstr_or_namelist):
    if isinstance(regex_or_regexstr_or_namelist, basestring):
        return re.compile(regex_or_regexstr_or_namelist).match
    elif isinstance(regex_or_regexstr_or_namelist, (list, tuple)):
        return regex_or_regexstr_or_namelist.__contains__
    elif isinstance(regex_or_regexstr_or_namelist, RegexType):
        return regex_or_regexstr_or_namelist.match
    else:
        raise TypeError("Unacceptable methods spec %r." % regex_or_regexstr_or_namelist)


class Sentinel(object):
    def __init__(self, name, doc=''):
        self.name = name
        self.__doc__ = doc

    def __repr__(self):
        if not self.__doc__:
            return "%s" % self.name
        else:
            return "%s: %s" % (self.name, self.__doc__)
    __str__ = __repr__


def container(name):
    def __init__(self, value):
        self.value = value

    return type(name, (object,), {
        '__slots__': 'value',
        '__init__': __init__,
        '__str__': lambda self: "%s(%s)" % (name, self.value),
        '__repr__': lambda self: "%s(%r)" % (name, self.value),
        '__eq__': lambda self, other: type(self) is type(other) and self.value == other.value,
    })


def mimic(wrapper, func, module=None):
    try:
        wrapper.__name__ = func.__name__
    except (TypeError, AttributeError):
        pass
    try:
        wrapper.__module__ = module or func.__module__
    except (TypeError, AttributeError):
        pass
    try:
        wrapper.__doc__ = func.__doc__
    except (TypeError, AttributeError):
        pass
    return wrapper


representers = {
    tuple: lambda obj, aliases: "(%s%s)" % (', '.join(repr_ex(i) for i in obj), ',' if len(obj) == 1 else ''),
    list: lambda obj, aliases: "[%s]" % ', '.join(repr_ex(i) for i in obj),
    set: lambda obj, aliases: "set([%s])" % ', '.join(repr_ex(i) for i in obj),
    frozenset: lambda obj, aliases: "set([%s])" % ', '.join(repr_ex(i) for i in obj),
    deque: lambda obj, aliases: "collections.deque([%s])" % ', '.join(repr_ex(i) for i in obj),
    dict: lambda obj, aliases: "{%s}" % ', '.join(
        "%s: %s" % (repr_ex(k), repr_ex(v)) for k, v in (obj.items() if PY3 else obj.iteritems())
    ),
}


def _make_fixups():
    for obj in ('os.stat_result', 'grp.struct_group', 'pwd.struct_passwd'):
        mod, attr = obj.split('.')
        try:
            yield getattr(__import__(mod), attr), lambda obj, aliases, prefix=obj: "%s(%r)" % (
                prefix,
                obj.__reduce__()[1][0]
            )
        except ImportError:
            continue
representers.update(_make_fixups())


def repr_ex(obj, aliases=()):
    kind, ident = type(obj), id(obj)
    if isinstance(kind, BaseException):
        return "%s(%s)" % (qualname(type(obj)), ', '.join(repr_ex(i, aliases) for i in obj.args))
    elif isclass(obj):
        return qualname(obj)
    elif kind in representers:
        return representers[kind](obj, aliases)
    elif ident in aliases:
        return aliases[ident][0]
    else:
        return repr(obj)
