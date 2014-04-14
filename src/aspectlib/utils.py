from __future__ import print_function

import re

RegexType = type(re.compile(""))


def qualname(obj):
    return '%s.%s' % (obj.__module__, obj.__name__)


def force_bind(func):
    def bound(self, *args, **kwargs):  # pylint: disable=W0613
        return func(*args, **kwargs)
    bound.__name__ = func.__name__
    bound.__doc__ = func.__doc__
    return bound


def make_method_matcher(regex_or_regexstr_or_namelist):
    if isinstance(regex_or_regexstr_or_namelist, (str, unicode)):
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
