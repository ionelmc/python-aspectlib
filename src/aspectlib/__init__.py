from __future__ import print_function
try:
    import __builtin__
except ImportError:
    import builtins as __builtin__
import platform
import sys
import warnings
from collections import deque
from functools import wraps
from itertools import chain
from logging import getLogger

from types import FunctionType
from types import GeneratorType
from types import MethodType

try:
    from types import ClassType
except ImportError:
    ClassType = type

logger = getLogger(__name__)

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2
PYPY = platform.python_implementation() == 'PyPy'

if PY3:
    unicode = str

DEFAULT_FALSE = object()
DEFAULT_TRUE = object()


class Proceed(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Return(object):
    def __init__(self, value):
        self.value = value


class Aspect(object):
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


class Entanglement(object):  # pylint: disable=C0103
    def __init__(self, rollbacks):
        self._rollbacks = rollbacks

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for rollback in self._rollbacks:
            rollback()

    rollback = __exit__

def _apply(aspect, function):
    logger.debug('Applying aspect %s to function %s.', aspect, function)
    wrapper = aspect(function)
    assert callable(wrapper), 'Aspect %s did not return a callable (it return %s).' % (aspect, wrapper)
    return wrapper


def weave(target, aspect,
          skip_magic_methods=DEFAULT_TRUE,
          skip_subclasses=DEFAULT_FALSE,
          on_init=DEFAULT_FALSE,
          skip_methods=(),
          only_methods=None):

    if only_methods and skip_methods:
        raise RuntimeError("You can't use both `skip_methods` and `only_methods`.")
    return Entanglement(_weave(
        target, aspect,
        skip_magic_methods=skip_magic_methods,
        skip_subclasses=skip_subclasses,
        on_init=on_init,
        skip_methods=skip_methods,
        only_methods=only_methods
    ))


def _patch_module(mod, name, value, replacement):
    rollbacks = []
    seen = False
    location = replacement.__module__ = mod.__name__
    for alias in dir(mod):
        if hasattr(mod, alias):
            obj = getattr(mod, alias)
            if obj is value:
                logger.debug(" * Saving %s on %s.%s ...", replacement, location, alias)
                setattr(mod, alias, replacement)
                rollbacks.append(lambda alias=alias: setattr(mod, alias, value))
                if alias == name:
                    seen = True
            elif alias == name:
                raise AssertionError("%s.%s = %s is not %s." % (location, alias, obj, value))

    if not seen:
        warnings.warn('Setting %s.%s to %s. There was no previous definition, probably patching the wrong module.' % (
            location, name, replacement
        ))
        logger.debug(" * Saving %s on %s.%s ...", replacement, location, name)
        setattr(mod, name, replacement)
        rollbacks.append(lambda: setattr(mod, name, value))
    return rollbacks


def _silly_bind(func):
    def bound(self, *args, **kwargs):
        return func(*args, **kwargs)
    bound.__name__ = func.__name__
    bound.__doc__ = func.__doc__
    return bound


def _weave_module_function(mod, target, aspect, force_name=None):
    logger.debug("Weaving %r as plain function.", target)
    name = force_name or target.__name__
    assert getattr(mod, name) is target
    return _patch_module(mod, name, target, _apply(aspect, target))


def _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods):
    assert skip_magic_methods is DEFAULT_TRUE, "Can't use skip_methods=%r when target is not a class." % skip_magic_methods
    assert skip_subclasses is DEFAULT_FALSE, "Can't use skip_subclasses=%r when target is not a class." % skip_subclasses
    #assert on_init is DEFAULT_FALSE, "Can't use on_init=%r when target is not a class." % on_init
    assert not skip_methods, "Can't use skip_methods=%r when target is not a class." % skip_methods
    assert not only_methods, "Can't use only_methods=%r when target is not a class." % only_methods


def _weave(target, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods):
    assert callable(aspect), '%s must be an `Aspect` instance or be a callable.' % (aspect)
    assert target, "Can't weave falsy value %r." % target
    if isinstance(target, (list, tuple)):
        return list(chain.from_iterable(
            _weave(item, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
            for item in target
        ))
    elif isinstance(target, (unicode, str)):
        assert '.' in target, "Need at least a module in the target specification !"
        parts = target.split('.')
        for pos in reversed(range(1, len(parts))):
            mod, target = '.'.join(parts[:pos]), '.'.join(parts[pos:])
            try:
                __import__(mod)
                mod = sys.modules[mod]
            except ImportError:
                continue
            else:
                break
        logger.debug("Patching %s from %s ...", target, mod)
        obj = getattr(mod, target)
        if isinstance(obj, (type, ClassType)):
            logger.debug(" .. as a class %r.", obj)
            return _weave_class(
                obj, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods,
                force_module=mod, force_name=target
            )
        elif callable(obj):  # or isinstance(obj, FunctionType) ??
            logger.debug(" .. as a callable %r.", obj)
            _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
            return _weave_module_function(mod, obj, aspect, force_name=target)
        else:
            raise RuntimeError("Can't weave object %s of type %s" % (obj, type(obj)))

    name = getattr(target, '__name__', None)
    if name and getattr(__builtin__, name, None) is target:
        _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
        return _weave_module_function(__builtin__, target, aspect)
    elif PY3 and isinstance(target, MethodType):
        inst = target.__self__
        name = target.__name__
        logger.debug("Weaving %r (%s) as instance method.", target, name)
        _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
        func = getattr(inst, name)
        setattr(inst, name, aspect(func).__get__(inst, type(inst)))
        return lambda: delattr(inst, name),
    elif PY3 and isinstance(target, FunctionType):
        owner = __import__(target.__module__)
        path = deque(target.__qualname__.split('.')[:-1])
        while path:
            owner = getattr(owner, path.popleft())
        name = target.__name__
        logger.debug("Weaving %r (%s) as a property.", target, name)
        func = owner.__dict__[name]
        setattr(owner, name, _apply(aspect, target))
        return lambda: setattr(owner, name, target),
    elif PY2 and isinstance(target, FunctionType):
        _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
        return _weave_module_function(__import__(target.__module__), target, aspect)
    elif PY2 and isinstance(target, MethodType):
        if target.im_self:
            inst = target.im_self
            name = target.__name__
            logger.debug("Weaving %r (%s) as instance method.", target, name)
            _assert_no_class_options(skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
            func = getattr(inst, name)
            setattr(inst, name, _apply(aspect, func).__get__(inst, type(inst)))
            return lambda: delattr(inst, name),
        else:
            klass = target.im_class
            name = target.__name__
            return _weave(
                klass, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods=(name,)
            )
    elif isinstance(target, (type, ClassType)):
        return _weave_class(target, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
    else:
        raise RuntimeError("Can't weave object %s of type %s" % (target, type(target)))

def _weave_class(target, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods,
                 force_module=None, force_name=None):
    skip_magic_methods = True if skip_magic_methods is DEFAULT_TRUE else skip_magic_methods
    skip_subclasses = False if skip_subclasses is DEFAULT_FALSE else skip_subclasses
    on_init = False if on_init is DEFAULT_FALSE else on_init

    assert isinstance(target, (type, ClassType)), "Can't weave %r as a class." % target
    rollbacks = []
    if not skip_subclasses and hasattr(target, '__subclasses__'):
        for sub_class in target.__subclasses__():
            if not issubclass(sub_class, Fabric):
                rollbacks.extend(_weave_class(
                    sub_class, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods,
                    force_module=force_module, force_name=force_name
                ))
    if on_init:
        logger.debug("Weaving %r as class (on demand at __init__ time).", target)

        def __init__(self, *args, **kwargs):
            super(SubClass, self).__init__(*args, **kwargs)
            for name in dir(self):
                func = getattr(self, name, None)
                if only_methods and name not in only_methods:
                    continue
                elif func is None or skip_magic_methods and name.startswith('__') or name.endswith('__'):
                    continue
                elif name not in skip_methods and name not in wrappers and callable(func):
                    setattr(self, name, _apply(aspect, _silly_bind(func)).__get__(self, SubClass))
                else:
                    continue
        wrappers = {
            '__init__': __init__ if skip_magic_methods else _apply(aspect, __init__)
        }
        for name, func in target.__dict__.items():
            if only_methods and name not in only_methods:
                continue
            elif skip_magic_methods and name.startswith('__') and name.endswith('__'):
                continue
            elif isinstance(func, staticmethod):
                if hasattr(func, '__func__'):
                    wrappers[name] = staticmethod(_apply(aspect, func.__func__))
                else:
                    wrappers[name] = staticmethod(_apply(aspect, func.__get__(None, target)))
            elif isinstance(func, classmethod):
                if hasattr(func, '__func__'):
                    wrappers[name] = classmethod(_apply(aspect, func.__func__))
                else:
                    wrappers[name] = classmethod(_apply(aspect, func.__get__(None, target).im_func))
            else:
                continue
        logger.debug(" * Creating subclass with attributes %r", wrappers)
        name = force_name or target.__name__
        SubClass = type(name, (target, Fabric), wrappers)
        SubClass.__module__ = target.__module__
        mod = force_module or __import__(target.__module__)
        rollbacks.extend(_patch_module(mod, name, target, SubClass))
    else:
        logger.debug("Weaving %r as class.", target)
        original = {}
        for name, func in target.__dict__.items():
            if only_methods and name not in only_methods:
                continue
            elif name in skip_methods or skip_magic_methods and name.startswith('__') and name.endswith('__'):
                continue
            elif isinstance(func, staticmethod):
                if hasattr(func, '__func__'):
                    setattr(target, name, staticmethod(_apply(aspect, func.__func__)))
                else:
                    setattr(target, name, staticmethod(_apply(aspect, func.__get__(None, target))))
            elif isinstance(func, classmethod):
                if hasattr(func, '__func__'):
                    setattr(target, name, classmethod(_apply(aspect, func.__func__)))
                else:
                    setattr(target, name, classmethod(_apply(aspect, func.__get__(None, target).im_func)))
            elif callable(func):
                setattr(target, name, _apply(aspect, func))
            else:
                continue
            original[name] = func

        rollbacks.append(lambda: deque((
            setattr(target, name, func) for name, func in original.items()
        ), maxlen=0))

    return rollbacks
