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
from operator import setitem

from types import BuiltinFunctionType
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


class Entanglement(object):  # pylint: disable=C0103
    def __init__(self, rollbacks):
        self.rollbacks = rollbacks

    def merge(self, entanglement):
        self.rollbacks.extend(entanglement.rollbacks)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for rollback in self.rollbacks:
            rollback()


def _apply(aspect, function):
    logger.debug('Applying aspect %s to function %s.', aspect, function)
    wrapper = aspect(function)
    assert callable(wrapper), 'Aspect %s did not return a callable (it return %s).' % (aspect, wrapper)
    return wrapper


def weave(target, aspect, skip_magic_methods=True, skip_subclasses=False, on_init=False, skip_methods=(), only_methods=None):
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
        obj = getattr(mod, alias, None)
        if obj is value:
            logger.debug(" * Saving %s on %s.%s ...", replacement, location, alias)
            setattr(mod, alias, replacement)
            rollbacks.append(lambda alias=alias: setattr(mod, alias, value))
            if alias == name:
                seen = True
    if not seen:
        warnings.warn('Setting %s.%s to %s. There was no previous definition, probably patching the wrong module !')
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


def _weave_module(mod, target, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods):
    logger.debug("Weaving %r as plain function.", target)
    name = target.__name__
    assert getattr(mod, name) is target
    return _patch_module(mod, name, target, _apply(aspect, target))

def _weave(target, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods):
    assert callable(aspect), '%s must be an `Aspect` instance or be a callable.' % (aspect)
    if isinstance(target, (list, tuple)):
        return list(chain.from_iterable(
            _weave(item, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods)
            for item in target
        ))
    #elif isinstance(target, (unicode, str)):
    #    assert '.' in target, "Need at least a module in the target specification !"
    #    parts = target.split('.')
    #    for pos in reversed(range(1, len(parts))):
    #        mod, target = '.'.join(parts[:pos]), '.'.join(parts[pos:])
    #        try:
    #            mod = __import__(mod)
    #        except ImportError:
    #            continue
    name = getattr(target, '__name__', None)
    #print(name, name and getattr(__builtin__, name, None), target)
    if name and getattr(__builtin__, name, None) is target:
        return _weave_module(
            __builtin__, target, aspect,
            skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods
        )
    elif PY3 and isinstance(target, MethodType):
        inst = target.__self__
        name = target.__name__
        logger.debug("Weaving %r (%s) as instance method.", target, name)
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
        return _weave_module(
            __import__(target.__module__), target, aspect,
            skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods
        )
    elif PY2 and isinstance(target, MethodType):
        if target.im_self:
            inst = target.im_self
            name = target.__name__
            logger.debug("Weaving %r (%s) as instance method.", target, name)
            func = getattr(inst, name)
            setattr(inst, name, _apply(aspect, func).__get__(inst, type(inst)))
            return lambda: delattr(inst, name),
        else:
            klass = target.im_class
            name = target.__name__
            logger.debug("Weaving %r (%s) as class method.", target, name)
            func = klass.__dict__[name]
            setattr(klass, name, _apply(aspect, func))
            return lambda: setattr(klass, name, func),
    elif isinstance(target, (type, ClassType)):
        rollbacks = []
        if not skip_subclasses and hasattr(target, '__subclasses__'):
            for sub_class in target.__subclasses__():
                rollbacks.extend(_weave(
                    sub_class, aspect, skip_magic_methods, skip_subclasses, on_init, skip_methods, only_methods
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
            name = target.__name__
            SubClass = type(name, (target,), wrappers)
            SubClass.__module__ = target.__module__
            mod = __import__(target.__module__)
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
    else:
        raise RuntimeError("Can't weave object %s of type %s" % (target, type(target)))
