from __future__ import print_function

import platform
import re
import sys
from functools import wraps
from inspect import isclass


RegexType = type(re.compile(""))

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PYPY = platform.python_implementation() == 'PyPy'

if PY3:
    basestring = str
else:
    basestring = str, unicode

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')

DEBUG = False

def logf(logger_func):
    @wraps(logger_func)
    def log_wrapper(*args):
        if DEBUG:
            return logger_func(*args)
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


def make_repr(repr=repr):
    from collections import deque
    representers = {
        tuple: lambda o: "(%s%s)" % (', '.join(lookup(type(i), repr)(i) for i in o), ',' if len(o) == 1 else ''),
        list: lambda o: "[%s]" % ', '.join(lookup(type(i), repr)(i) for i in o),
        set: lambda o: "set([%s])" % ', '.join(lookup(type(i), repr)(i) for i in o),
        frozenset: lambda o: "set([%s])" % ', '.join(lookup(type(i), repr)(i) for i in o),
        deque: lambda o: "collections.deque([%s])" % ', '.join(lookup(type(i), repr)(i) for i in o),
        dict: lambda o: "{%s}" % ', '.join(
            "%s: %s" % (
                lookup(type(k), repr_ex)(k),
                lookup(type(v), repr_ex)(v),
            ) for k, v in (o.items() if PY3 else o.iteritems())
        ),
    }
    representers.update(
        (getattr(__import__(mod), attr), lambda o, prefix=obj: "%s(%r)" % (prefix, o.__reduce__()[1][0]))
        for obj in ('os.stat_result', 'grp.struct_group', 'pwd.struct_passwd')
        for mod, attr in (obj.split('.'),)
    )

    lookup = representers.get
    def repr_ex(o):
        return lookup(type(o), repr)(o)
    return repr_ex
repr_ex = make_repr()


def make_signature(name, args, kwargs, *resp):
    sig = '%s(%s%s%s)' % (
        name,
        ', '.join(repr(i) for i in args),
        ', ' if kwargs else '',
        ', '.join("%s=%r" % i for i in (kwargs.items() if isinstance(kwargs, dict) else kwargs)),
    )
    if resp:
        result, exception = resp
        if exception is None:
            return '%s == %s  # returns\n' % (sig, repr_ex(result))
        else:
            if isclass(exception):
                return '%s ** %s  # raises\n' % (sig, qualname(exception))
            else:
                return '%s ** %s(%s)  # raises\n' % (
                    sig,
                    qualname(type(exception)),
                    ', '.join(repr(i) for i in exception.args)
                )
    else:
        return sig

