from __future__ import print_function

import platform
import re
import sys
import warnings
from collections import deque
from functools import wraps
from inspect import isclass
from inspect import isfunction
from inspect import ismethod
from inspect import ismethoddescriptor
from inspect import isroutine
from logging import getLogger

from types import GeneratorType


__all__ = 'weave', 'Aspect', 'Proceed', 'Return', 'ALL_METHODS', 'NORMAL_METHODS'

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__  # pylint: disable=F0401

try:
    from types import ClassType
except ImportError:
    ClassType = type

logger = getLogger(__name__)

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PYPY = platform.python_implementation() == 'PyPy'

if PY3:
    unicode = str  # pylint: disable=W0622


class _Sentinel(object):
    def __init__(self, name, doc=''):
        self.name = name
        self.__doc__ = doc

    def __repr__(self):
        if not self.__doc__:
            return "%s" % self.name
        else:
            return "%s: %s" % (self.name, self.__doc__)
    __str__ = __repr__

UNSPECIFIED = _Sentinel('UNSPECIFIED')
ALL_METHODS = re.compile('.*')
NORMAL_METHODS = re.compile('(?!__.*__$)')
REGEX_TYPE = type(NORMAL_METHODS)
VALID_IDENTIFIER = re.compile('^[^\W\d]\w*$', re.UNICODE if PY3 else 0)

class Proceed(object):
    """
    Instructs the Aspect Calls to call the decorated function. Can be used multiple times.

    If not used as an instance then the default args and kwargs are used.
    """
    __slots__ = 'args', 'kwargs'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Return(object):
    """
    Instructs the Aspect to return a value.
    """
    __slots__ = 'value',

    def __init__(self, value):
        self.value = value


class Aspect(object):
    """
    Container for the advice yielding generator. Can be used as a decorator on other function to change behavior
    according to the advices yielded from the generator.
    """
    __slots__ = 'advise_function'

    def __init__(self, advise_function):
        assert callable(advise_function)
        self.advise_function = advise_function

    def __call__(self, cutpoint_function):
        @wraps(cutpoint_function)
        def advice_wrapper(*args, **kwargs):
            advisor = self.advise_function(*args, **kwargs)
            if not isinstance(advisor, GeneratorType):
                raise RuntimeError("advise_function %s did not return a generator." % self.advise_function)
            advice = advisor.send(None)
            while True:
                if advice is Proceed or advice is None or isinstance(advice, Proceed):
                    if advice is not Proceed:
                        args = advice.args
                        kwargs = advice.kwargs
                    try:
                        result = cutpoint_function(*args, **kwargs)
                    except Exception:
                        advice = advisor.throw(*sys.exc_info())
                    else:
                        try:
                            advice = advisor.send(result)
                        except StopIteration:
                            return result
                elif advice is Return:
                    return
                elif isinstance(advice, Return):
                    return advice.value
        return advice_wrapper


class Fabric(object):
    pass


class Rollback(object):
    """
    When called, rollbacks all the patches and changes the :func:`weave` has done.
    """
    __slots__ = '_rollbacks'

    def __init__(self, rollback=None):
        if rollback is None:
            self._rollbacks = []
        elif isinstance(rollback, (list, tuple)):
            self._rollbacks = rollback
        else:
            self._rollbacks = [rollback]

    def merge(self, other):
        self._rollbacks.append(other)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for rollback in self._rollbacks:
            rollback()

    rollback = __call__ = __exit__


def checked_apply(aspect, function):
    logger.debug('Applying aspect %s to function %s.', aspect, function)
    wrapper = aspect(function)
    assert callable(wrapper), 'Aspect %s did not return a callable (it return %s).' % (aspect, wrapper)
    return wrapper


def check_name(name):
    if not VALID_IDENTIFIER.match(name):
        raise SyntaxError(
            "Could not match %r to %r. It should be a string of "
            "letters, numbers and underscore that starts with a letter or underscore." % (
                name, VALID_IDENTIFIER.pattern
            )
        )


def weave(target, aspect, **options):
    """
    Send a message to a recipient

    :param target: The object to weave
    :type target: string, class, instance, function or builtin

    :param aspect: The aspect to apply to the object
    :type target: :py:obj:`aspectlib.Aspect` or function decorator

    :param bool subclasses:
        If ``True``, subclasses of target are weaved. *Only available for classes*

    :param bool aliases:
        If ``True``, aliases of target are replaced.

    :param bool lazy:
        If ``True`` only patch target's ``__init__``, the rest of the methods are patched after ``__init__`` is
        called. *Only available for classes*

    :param methods: Methods from target to patch. *Only available for classes*
    :type methods: list or regex or string

    :returns:
        :class:`aspectlib.Rollback` instance

    :raises TypeError:
        If target is a unacceptable object, or the specified options are not available for that type of object.

    """
    assert callable(aspect), '%s must be an `Aspect` instance or be a callable.' % (aspect)
    assert target, "Can't weave falsy value %r." % target
    if isinstance(target, (list, tuple)):
        return Rollback([
            weave(item, aspect, **options) for item in target
        ])
    elif isinstance(target, (unicode, str)):
        assert '.' in target, "Need at least a module in the target specification !"
        parts = target.split('.')
        for part in parts:
            check_name(part)

        for pos in reversed(range(1, len(parts))):
            owner, name = '.'.join(parts[:pos]), '.'.join(parts[pos:])
            try:
                __import__(owner)
                owner = sys.modules[owner]
            except ImportError:
                continue
            else:
                break
        else:
            raise ImportError("Could not import %r. Last try was for %s" % (target, owner))

        if '.' in name:
            path, name = name.rsplit('.', 1)
            path = deque(path.split('.'))
            while path:
                owner = getattr(owner, path.popleft())

        logger.debug("Patching %s from %s ...", name, owner)
        obj = getattr(owner, name)
        if isinstance(obj, (type, ClassType)):
            logger.debug(" .. as a class %r.", obj)
            return weave_class(
                obj, aspect,
                owner=owner, name=name, **options
            )
        elif callable(obj):  # or isinstance(obj, FunctionType) ??
            logger.debug(" .. as a callable %r.", obj)
            return weave_module_function(owner, obj, aspect, force_name=name, **options)
        else:
            raise TypeError("Can't weave object %s of type %s" % (obj, type(obj)))
    name = getattr(target, '__name__', None)
    if name and getattr(__builtin__, name, None) is target:
        return weave_module_function(__builtin__, target, aspect, **options)
    elif PY3 and ismethod(target):
        inst = target.__self__
        name = target.__name__
        logger.debug("Weaving %r (%s) as instance method.", target, name)
        assert not options, "keyword arguments are not supported when weaving instance methods."
        func = getattr(inst, name)
        setattr(inst, name, checked_apply(aspect, func).__get__(inst, type(inst)))
        return Rollback(lambda: delattr(inst, name))
    elif PY3 and isfunction(target):
        owner = __import__(target.__module__)
        path = deque(target.__qualname__.split('.')[:-1])
        while path:
            owner = getattr(owner, path.popleft())
        name = target.__name__
        logger.debug("Weaving %r (%s) as a property.", target, name)
        func = owner.__dict__[name]
        return patch_module(owner, name, checked_apply(aspect, func), func, **options)
    elif PY2 and isfunction(target):
        return weave_module_function(__import__(target.__module__), target, aspect, **options)
    elif PY2 and ismethod(target):
        if target.im_self:
            inst = target.im_self
            name = target.__name__
            logger.debug("Weaving %r (%s) as instance method.", target, name)
            assert not options, "keyword arguments are not supported when weaving instance methods."
            func = getattr(inst, name)
            setattr(inst, name, checked_apply(aspect, func).__get__(inst, type(inst)))
            return Rollback(lambda: delattr(inst, name))
        else:
            klass = target.im_class
            name = target.__name__
            return weave(klass, aspect, methods='%s$' % name, **options)
    elif isclass(target):
        return weave_class(target, aspect, **options)
    else:
        raise RuntimeError("Can't weave object %s of type %s" % (target, type(target)))


def rewrap_method(func, klass, aspect):
    if isinstance(func, staticmethod):
        if hasattr(func, '__func__'):
            return staticmethod(checked_apply(aspect, func.__func__))
        else:
            return staticmethod(checked_apply(aspect, func.__get__(None, klass)))
    elif isinstance(func, classmethod):
        if hasattr(func, '__func__'):
            return classmethod(checked_apply(aspect, func.__func__))
        else:
            return classmethod(checked_apply(aspect, func.__get__(None, klass).im_func))
    else:
        return checked_apply(aspect, func)


def weave_class(klass, aspect, methods=NORMAL_METHODS, subclasses=True, lazy=False,
                owner=None, name=None, aliases=True):

    assert isclass(klass), "Can't weave %r. Must be a class." % klass
    entanglement = Rollback()
    if isinstance(methods, (str, unicode)):
        method_matches = re.compile(methods).match
    elif isinstance(methods, (list, tuple)):
        method_matches = methods.__contains__
    elif isinstance(methods, REGEX_TYPE):
        method_matches = methods.match
    else:
        raise TypeError("Unacceptable methods spec %r." % methods)

    if subclasses and hasattr(klass, '__subclasses__'):
        for sub_class in klass.__subclasses__():
            if not issubclass(sub_class, Fabric):
                entanglement.merge(weave_class(sub_class, aspect, methods=methods, subclasses=subclasses, lazy=lazy))
    if lazy:
        logger.debug("Weaving %r as class (on demand at __init__ time).", klass)

        def __init__(self, *args, **kwargs):
            super(SubClass, self).__init__(*args, **kwargs)
            for attr in dir(self):
                func = getattr(self, attr, None)
                if method_matches(attr) and attr not in wrappers and callable(func):
                    setattr(self, attr, checked_apply(aspect, force_bind(func)).__get__(self, SubClass))

        wrappers = {
            '__init__': checked_apply(aspect, __init__) if method_matches('__init__') else __init__
        }
        for attr, func in klass.__dict__.items():
            if method_matches(attr):
                if ismethoddescriptor(func):
                    wrappers[attr] = rewrap_method(func, klass, aspect)

        logger.debug(" * Creating subclass with attributes %r", wrappers)
        name = name or klass.__name__
        SubClass = type(name, (klass, Fabric), wrappers)
        SubClass.__module__ = klass.__module__
        module = owner or __import__(klass.__module__)
        entanglement.merge(patch_module(module, name, SubClass, original=klass, aliases=aliases))
    else:
        logger.debug("Weaving %r as class.", klass)
        original = {}
        for attr, func in klass.__dict__.items():
            if method_matches(attr):
                if isroutine(func):
                    setattr(klass, attr, rewrap_method(func, klass, aspect))
                else:
                    continue
                original[attr] = func

        entanglement.merge(lambda: deque((
            setattr(klass, attr, func) for attr, func in original.items()
        ), maxlen=0))

    return entanglement


def patch_module(module, name, replacement, original=UNSPECIFIED, aliases=True):
    rollback = Rollback()
    seen = False
    original = getattr(module, name) if original is UNSPECIFIED else original
    location = replacement.__module__ = module.__name__
    for alias in dir(module):
        if hasattr(module, alias):
            obj = getattr(module, alias)
            if obj is original:
                if aliases or alias == name:
                    logger.debug(" * Saving %s on %s.%s ...", replacement, location, alias)
                    setattr(module, alias, replacement)
                    rollback.merge(lambda alias=alias: setattr(module, alias, original))
                if alias == name:
                    seen = True
            elif alias == name:
                if ismethod(obj):
                    logger.debug(" * Saving %s on %s.%s ...", replacement, location, alias)
                    setattr(module, alias, replacement)
                    rollback.merge(lambda alias=alias: setattr(module, alias, original))
                else:
                    raise AssertionError("%s.%s = %s is not %s." % (location, alias, obj, original))

    if not seen:
        warnings.warn('Setting %s.%s to %s. There was no previous definition, probably patching the wrong module.' % (
            location, name, replacement
        ))
        logger.debug(" * Saving %s on %s.%s ...", replacement, location, name)
        setattr(module, name, replacement)
        rollback.merge(lambda: setattr(module, name, original))
    return rollback


def force_bind(func):
    def bound(self, *args, **kwargs):  # pylint: disable=W0613
        return func(*args, **kwargs)
    bound.__name__ = func.__name__
    bound.__doc__ = func.__doc__
    return bound


def weave_module_function(mod, target, aspect, force_name=None, **options):
    logger.debug("Weaving %r as plain function.", target)
    name = force_name or target.__name__
    return patch_module(mod, name, checked_apply(aspect, target), original=target, **options)
