from __future__ import print_function

import re
import sys
import platform

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


def mimic(wrapper, func):
    try:
        wrapper.__name__ = func.__name__
    except (TypeError, AttributeError):
        pass
    try:
        wrapper.__module__ = func.__module__
    except (TypeError, AttributeError):
        pass
    try:
        wrapper.__doc__ = func.__doc__
    except (TypeError, AttributeError):
        pass
    return wrapper
