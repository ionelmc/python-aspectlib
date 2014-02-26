from __future__ import print_function
import sys
from collections import deque
from functools import wraps
from logging import getLogger
from operator import setitem
try:
    from types import ClassType
except ImportError:
    ClassType = type
from types import FunctionType
from types import GeneratorType
from types import MethodType

logger = getLogger(__name__)

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2


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
                if advice is Proceed or isinstance(advice, Proceed):
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
    def __init__(self, rollback):
        self.rollbacks = [rollback]

    def merge(self, entanglement):
        self.rollbacks.extend(entanglement.rollbacks)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for rollback in self.rollbacks:
            rollback()

def weave(target, aspect, skip_magic_methods=True, skip_subclasses=False):
    assert isinstance(aspect, Aspect), '%s must be an `aspect` instance.' % (aspect)
    if PY3 and isinstance(target, MethodType):
        inst = target.__self__
        name = target.__name__
        logger.debug("Weaving %r (%s) as instance method.", target, name)
        func = getattr(inst, name)
        setattr(inst, name, aspect(func).__get__(inst, type(inst)))
        return Entanglement(lambda: delattr(inst, name))
    if PY3 and isinstance(target, FunctionType):
        owner = __import__(target.__module__)
        path = deque(target.__qualname__.split('.')[:-1])
        while path:
            owner = getattr(owner, path.popleft())
        name = target.__name__
        logger.debug("Weaving %r (%s) as a property.", target, name)
        func = owner.__dict__[name]
        setattr(owner, name, aspect(target))
        return Entanglement(lambda: setattr(owner, name, target))
    elif PY2 and isinstance(target, FunctionType):
        logger.debug("Weaving %r as plain function.", target)
        mod = __import__(target.__module__)
        name = target.__name__
        assert getattr(mod, name) is target
        setattr(mod, name, aspect(target))
        return Entanglement(lambda: setattr(mod, name, target))
    elif PY2 and isinstance(target, MethodType):
        if target.im_self:
            inst = target.im_self
            name = target.__name__
            logger.debug("Weaving %r (%s) as instance method.", target, name)
            func = getattr(inst, name)
            setattr(inst, name, aspect(func).__get__(inst, type(inst)))
            return Entanglement(lambda: delattr(inst, name))
        else:
            klass = target.im_class
            name = target.__name__
            logger.debug("Weaving %r (%s) as class method.", target, name)
            func = klass.__dict__[name]
            setattr(klass, name, aspect(func))
            return Entanglement(lambda: setattr(klass, name, func))
    elif isinstance(target, (type, ClassType)):
        logger.debug("Weaving %r as class.", target)
        original = {}
        for name, func in target.__dict__.items():
            if skip_magic_methods and name.startswith('__') or name.endswith('__'):
                continue
            if callable(func):
                setattr(target, name, aspect(func))
            elif isinstance(func, staticmethod):
                if hasattr(func, '__func__'):
                    setattr(target, name, staticmethod(aspect(func.__func__)))
                else:
                    setattr(target, name, staticmethod(aspect(func.__get__(None, target))))
            elif isinstance(func, classmethod):
                if hasattr(func, '__func__'):
                    setattr(target, name, classmethod(aspect(func.__func__)))
                else:
                    setattr(target, name, classmethod(aspect(func.__get__(None, target).im_func)))
            else:
                continue
            original[name] = func

        entanglement = Entanglement(lambda: deque((
            setattr(target, name, func) for name, func in original.items()
        ), maxlen=0))
        if not skip_subclasses and hasattr(target, '__subclasses__'):
            for sub in target.__subclasses__():
                entanglement.merge(weave(sub, aspect, skip_magic_methods=skip_magic_methods))
        return entanglement
    else:
        raise RuntimeError("Can't weave object %s of type %s" % (target, type(target)))
