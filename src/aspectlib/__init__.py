from __future__ import print_function

import re
import sys
import warnings
from collections import deque
from inspect import isclass
from inspect import isfunction
from inspect import isgenerator
from inspect import isgeneratorfunction
from inspect import ismethod
from inspect import ismethoddescriptor
from inspect import ismodule
from inspect import isroutine
try:
    from types import InstanceType
except ImportError:
    InstanceType = None
from functools import partial
from logging import getLogger

from .utils import basestring
from .utils import force_bind
from .utils import logf
from .utils import make_method_matcher
from .utils import mimic
from .utils import PY2
from .utils import PY3
from .utils import Sentinel

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__  # pylint: disable=F0401

try:
    from types import ClassType
except ImportError:
    ClassType = type


__all__ = 'weave', 'Aspect', 'Proceed', 'Return', 'ALL_METHODS', 'NORMAL_METHODS', 'ABSOLUTELY_ALL_METHODS'
__version__ = '1.3.3'

logger = getLogger(__name__)
logdebug = logf(logger.debug)
logexception = logf(logger.exception)

UNSPECIFIED = Sentinel('UNSPECIFIED')
ABSOLUTELLY_ALL_METHODS = re.compile('.*')
ABSOLUTELY_ALL_METHODS = ABSOLUTELLY_ALL_METHODS
ALL_METHODS = re.compile('(?!__getattribute__$)')
NORMAL_METHODS = re.compile('(?!__.*__$)')
VALID_IDENTIFIER = re.compile(r'^[^\W\d]\w*$', re.UNICODE if PY3 else 0)


class UnacceptableAdvice(RuntimeError):
    pass


class ExpectedGenerator(TypeError):
    pass


class ExpectedGeneratorFunction(ExpectedGenerator):
    pass


class ExpectedAdvice(TypeError):
    pass


class UnsupportedType(TypeError):
    pass


class Proceed(object):
    """
    Instruction for calling the decorated function. Can be used multiple times.

    If not used as an instance then the default args and kwargs are used.
    """
    __slots__ = 'args', 'kwargs'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Return(object):
    """
    Instruction for returning a *optional* value.

    If not used as an instance then ``None`` is returned.
    """
    __slots__ = 'value',

    def __init__(self, value):
        self.value = value


class Aspect(object):
    """
    Container for the advice yielding generator. Can be used as a decorator on other function to change behavior
    according to the advices yielded from the generator.

    Args:
        advising_function (generator function): A generator function that yields :ref:`advices`.
        bind (bool): A convenience flag so you can access the cutpoint function (you'll get it as an argument).

    Usage::

        >>> @Aspect
        ... def my_decorator(*args, **kwargs):
        ...     print("Got called with args: %s kwargs: %s" % (args, kwargs))
        ...     result = yield
        ...     print(" ... and the result is: %s" % (result,))
        >>> @my_decorator
        ... def foo(a, b, c=1):
        ...     print((a, b, c))
        >>> foo(1, 2, c=3)
        Got called with args: (1, 2) kwargs: {'c': 3}
        (1, 2, 3)
         ... and the result is: None

    Normally you don't have access to the cutpoints (the functions you're going to use the aspect/decorator on) because
    you don't and should not call them directly. There are situations where you'd want to get the name or other data
    from the function. This is where you use the ``bind=True`` option::

        >>> @Aspect(bind=True)
        ... def my_decorator(cutpoint, *args, **kwargs):
        ...     print("`%s` got called with args: %s kwargs: %s" % (cutpoint.__name__, args, kwargs))
        ...     result = yield
        ...     print(" ... and the result is: %s" % (result,))
        >>> @my_decorator
        ... def foo(a, b, c=1):
        ...     print((a, b, c))
        >>> foo(1, 2, c=3)
        `foo` got called with args: (1, 2) kwargs: {'c': 3}
        (1, 2, 3)
         ... and the result is: None

    """
    __slots__ = 'advising_function', 'bind'

    def __new__(cls, advising_function=UNSPECIFIED, bind=False):
        if advising_function is UNSPECIFIED:
            return partial(cls, bind=bind)
        else:
            self = super(Aspect, cls).__new__(cls)
            self.__init__(advising_function, bind)
            return self

    def __init__(self, advising_function, bind=False):
        if not isgeneratorfunction(advising_function):
            raise ExpectedGeneratorFunction("advising_function %s must be a generator function." % advising_function)
        self.advising_function = advising_function
        self.bind = bind

    def __call__(self, cutpoint_function):
        if isgeneratorfunction(cutpoint_function):
            if PY3:
                from aspectlib.py3support import decorate_advising_generator_py3
                return decorate_advising_generator_py3(self.advising_function, cutpoint_function, self.bind)
            else:
                def advising_generator_wrapper(*args, **kwargs):
                    if self.bind:
                        advisor = self.advising_function(cutpoint_function, *args, **kwargs)
                    else:
                        advisor = self.advising_function(*args, **kwargs)
                    if not isgenerator(advisor):
                        raise ExpectedGenerator("advising_function %s did not return a generator." % self.advising_function)
                    try:
                        advice = next(advisor)
                        while True:
                            logdebug('Got advice %r from %s', advice, self.advising_function)
                            if advice is Proceed or advice is None or isinstance(advice, Proceed):
                                if isinstance(advice, Proceed):
                                    args = advice.args
                                    kwargs = advice.kwargs
                                gen = cutpoint_function(*args, **kwargs)
                                try:
                                    try:
                                        generated = next(gen)
                                    except StopIteration as exc:
                                        logexception("The cutpoint has been exhausted (early).")
                                        result = exc.args
                                        if result:
                                            if len(result) == 1:
                                                result = exc.args[0]
                                        else:
                                            result = None
                                    else:
                                        while True:
                                            try:
                                                sent = yield generated
                                            except GeneratorExit as exc:
                                                logexception("Got GeneratorExit while consuming the cutpoint")
                                                gen.close()
                                                raise exc
                                            except BaseException as exc:
                                                logexception("Got exception %r. Throwing it the cutpoint", exc)
                                                try:
                                                    generated = gen.throw(*sys.exc_info())
                                                except StopIteration as exc:
                                                    logexception("The cutpoint has been exhausted.")
                                                    result = exc.args
                                                    if result:
                                                        if len(result) == 1:
                                                            result = exc.args[0]
                                                    else:
                                                        result = None
                                                    break
                                            else:
                                                try:
                                                    if sent is None:
                                                        generated = next(gen)
                                                    else:
                                                        generated = gen.send(sent)
                                                except StopIteration as exc:
                                                    logexception("The cutpoint has been exhausted.")
                                                    result = exc.args
                                                    if result:
                                                        if len(result) == 1:
                                                            result = exc.args[0]
                                                    else:
                                                        result = None
                                                    break
                                except BaseException as exc:
                                    advice = advisor.throw(*sys.exc_info())
                                else:
                                    try:
                                        advice = advisor.send(result)
                                    except StopIteration:
                                        raise StopIteration(result)
                                finally:
                                    gen.close()
                            elif advice is Return:
                                return
                            elif isinstance(advice, Return):
                                raise StopIteration(advice.value)
                            else:
                                raise UnacceptableAdvice("Unknown advice %s" % advice)
                    finally:
                        advisor.close()
                return mimic(advising_generator_wrapper, cutpoint_function)
        else:
            def advising_function_wrapper(*args, **kwargs):
                if self.bind:
                    advisor = self.advising_function(cutpoint_function, *args, **kwargs)
                else:
                    advisor = self.advising_function(*args, **kwargs)
                if not isgenerator(advisor):
                    raise ExpectedGenerator("advising_function %s did not return a generator." % self.advising_function)
                try:
                    advice = next(advisor)
                    while True:
                        logdebug('Got advice %r from %s', advice, self.advising_function)
                        if advice is Proceed or advice is None or isinstance(advice, Proceed):
                            if isinstance(advice, Proceed):
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
                        else:
                            raise UnacceptableAdvice("Unknown advice %s" % advice)
                finally:
                    advisor.close()
            return mimic(advising_function_wrapper, cutpoint_function)


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

    def merge(self, *others):
        self._rollbacks.extend(others)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        for rollback in self._rollbacks:
            rollback()

    rollback = __call__ = __exit__


class ObjectBag(object):
    def __init__(self):
        self._objects = {}

    def has(self, obj):
        if id(obj) in self._objects:
            logdebug('  --- ObjectBag ALREADY HAS %r', obj)
            return True
        else:
            self._objects[id(obj)] = obj
            return False

BrokenBag = type('BrokenBag', (), dict(has=lambda self, obj: False))()


class EmptyRollback(object):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    rollback = __call__ = __exit__

Nothing = EmptyRollback()


def _checked_apply(aspects, function, module=None):
    logdebug('  applying aspects %s to function %s.', aspects, function)
    if callable(aspects):
        wrapper = aspects(function)
        assert callable(wrapper), 'Aspect %s did not return a callable (it return %s).' % (aspects, wrapper)
    else:
        wrapper = function
        for aspect in aspects:
            wrapper = aspect(wrapper)
            assert callable(wrapper), 'Aspect %s did not return a callable (it return %s).' % (aspect, wrapper)
    return mimic(wrapper, function, module=module)


def _check_name(name):
    if not VALID_IDENTIFIER.match(name):
        raise SyntaxError(
            "Could not match %r to %r. It should be a string of "
            "letters, numbers and underscore that starts with a letter or underscore." % (
                name, VALID_IDENTIFIER.pattern
            )
        )


def weave(target, aspects, **options):
    """
    Send a message to a recipient

    Args:
        target (string, class, instance, function or builtin):
            The object to weave.
        aspects (:py:obj:`aspectlib.Aspect`, function decorator or list of):
            The aspects to apply to the object.
        subclasses (bool):
            If ``True``, subclasses of target are weaved. *Only available for classes*
        aliases (bool):
            If ``True``, aliases of target are replaced.
        lazy (bool):
            If ``True`` only target's ``__init__`` method is patched, the rest of the methods are patched after
            ``__init__`` is called. *Only available for classes*.
        methods (list or regex or string):
            Methods from target to patch. *Only available for classes*

    Returns:
        aspectlib.Rollback: An object that can rollback the patches.

    Raises:
        TypeError: If target is a unacceptable object, or the specified options are not available for that type of
            object.

    .. versionchanged:: 0.4.0

        Replaced `only_methods`, `skip_methods`, `skip_magicmethods` options with `methods`.
        Renamed `on_init` option to `lazy`.
        Added `aliases` option.
        Replaced `skip_subclasses` option with `subclasses`.
    """
    if not callable(aspects):
        if not hasattr(aspects, '__iter__'):
            raise ExpectedAdvice('%s must be an `Aspect` instance, a callable or an iterable of.' % aspects)
        for obj in aspects:
            if not callable(obj):
                raise ExpectedAdvice('%s must be an `Aspect` instance or a callable.' % obj)
    assert target, "Can't weave falsy value %r." % target
    logdebug("weave (target=%s, aspects=%s, **options=%s)", target, aspects, options)

    bag = options.setdefault('bag', ObjectBag())

    if isinstance(target, (list, tuple)):
        return Rollback([
            weave(item, aspects, **options) for item in target
        ])
    elif isinstance(target, basestring):
        parts = target.split('.')
        for part in parts:
            _check_name(part)

        if len(parts) == 1:
            __import__(part)
            return weave_module(sys.modules[part], aspects, **options)

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

        logdebug("@ patching %s from %s ...", name, owner)
        obj = getattr(owner, name)

        if isinstance(obj, (type, ClassType)):
            logdebug("   .. as a class %r.", obj)
            return weave_class(
                obj, aspects,
                owner=owner, name=name, **options
            )
        elif callable(obj):  # or isinstance(obj, FunctionType) ??
            logdebug("   .. as a callable %r.", obj)
            if bag.has(obj):
                return Nothing
            return patch_module_function(owner, obj, aspects, force_name=name, **options)
        else:
            return weave(obj, aspects, **options)

    name = getattr(target, '__name__', None)
    if name and getattr(__builtin__, name, None) is target:
        if bag.has(target):
            return Nothing
        return patch_module_function(__builtin__, target, aspects, **options)
    elif PY3 and ismethod(target):
        if bag.has(target):
            return Nothing
        inst = target.__self__
        name = target.__name__
        logdebug("@ patching %r (%s) as instance method.", target, name)
        func = getattr(inst, name)
        setattr(inst, name, _checked_apply(aspects, func).__get__(inst, type(inst)))
        return Rollback(lambda: delattr(inst, name))
    elif PY3 and isfunction(target):
        if bag.has(target):
            return Nothing
        owner = __import__(target.__module__)
        path = deque(target.__qualname__.split('.')[:-1])
        while path:
            owner = getattr(owner, path.popleft())
        name = target.__name__
        logdebug("@ patching %r (%s) as a property.", target, name)
        func = owner.__dict__[name]
        return patch_module(owner, name, _checked_apply(aspects, func), func, **options)
    elif PY2 and isfunction(target):
        if bag.has(target):
            return Nothing
        return patch_module_function(__import__(target.__module__), target, aspects, **options)
    elif PY2 and ismethod(target):
        if target.im_self:
            if bag.has(target):
                return Nothing
            inst = target.im_self
            name = target.__name__
            logdebug("@ patching %r (%s) as instance method.", target, name)
            func = getattr(inst, name)
            setattr(inst, name, _checked_apply(aspects, func).__get__(inst, type(inst)))
            return Rollback(lambda: delattr(inst, name))
        else:
            klass = target.im_class
            name = target.__name__
            return weave(klass, aspects, methods='%s$' % name, **options)
    elif isclass(target):
        return weave_class(target, aspects, **options)
    elif ismodule(target):
        return weave_module(target, aspects, **options)
    elif type(target).__module__ not in ('builtins', '__builtin__') or InstanceType and isinstance(target, InstanceType):
        return weave_instance(target, aspects, **options)
    else:
        raise UnsupportedType("Can't weave object %s of type %s" % (target, type(target)))


def _rewrap_method(func, klass, aspect):
    if isinstance(func, staticmethod):
        if hasattr(func, '__func__'):
            return staticmethod(_checked_apply(aspect, func.__func__))
        else:
            return staticmethod(_checked_apply(aspect, func.__get__(None, klass)))
    elif isinstance(func, classmethod):
        if hasattr(func, '__func__'):
            return classmethod(_checked_apply(aspect, func.__func__))
        else:
            return classmethod(_checked_apply(aspect, func.__get__(None, klass).im_func))
    else:
        return _checked_apply(aspect, func)


def weave_instance(instance, aspect, methods=NORMAL_METHODS, lazy=False, bag=BrokenBag, **options):
    """
    Low-level weaver for instances.

    .. warning:: You should not use this directly.

    :returns: An :obj:`aspectlib.Rollback` object.
    """
    if bag.has(instance):
        return Nothing

    entanglement = Rollback()
    method_matches = make_method_matcher(methods)
    logdebug("weave_instance (module=%r, aspect=%s, methods=%s, lazy=%s, **options=%s)",
             instance, aspect, methods, lazy, options)

    def fixup(func):
        return func.__get__(instance, type(instance))
    fixed_aspect = aspect + [fixup] if isinstance(aspect, (list, tuple)) else [aspect, fixup]

    for attr in dir(instance):
        func = getattr(instance, attr)
        if method_matches(attr):
            if ismethod(func):
                if hasattr(func, '__func__'):
                    realfunc = func.__func__
                else:
                    realfunc = func.im_func
                entanglement.merge(
                    patch_module(instance, attr, _checked_apply(fixed_aspect, realfunc, module=None), **options)
                )
    return entanglement


def weave_module(module, aspect, methods=NORMAL_METHODS, lazy=False, bag=BrokenBag, **options):
    """
    Low-level weaver for "whole module weaving".

    .. warning:: You should not use this directly.

    :returns: An :obj:`aspectlib.Rollback` object.
    """
    if bag.has(module):
        return Nothing

    entanglement = Rollback()
    method_matches = make_method_matcher(methods)
    logdebug("weave_module (module=%r, aspect=%s, methods=%s, lazy=%s, **options=%s)",
             module, aspect, methods, lazy, options)

    for attr in dir(module):
        func = getattr(module, attr)
        if method_matches(attr):
            if isroutine(func):
                entanglement.merge(patch_module_function(module, func, aspect, force_name=attr, **options))
            elif isclass(func):
                entanglement.merge(
                    weave_class(func, aspect, owner=module, name=attr, methods=methods, lazy=lazy, bag=bag, **options),
                    #  it's not consistent with the other ways of weaving a class (it's never weaved as a routine).
                    #  therefore it's disabled until it's considered useful.
                    #  #patch_module_function(module, getattr(module, attr), aspect, force_name=attr, **options),
                )
    return entanglement


def weave_class(klass, aspect, methods=NORMAL_METHODS, subclasses=True, lazy=False,
                owner=None, name=None, aliases=True, bases=True, bag=BrokenBag):
    """
    Low-level weaver for classes.

    .. warning:: You should not use this directly.
    """
    assert isclass(klass), "Can't weave %r. Must be a class." % klass

    if bag.has(klass):
        return Nothing

    entanglement = Rollback()
    method_matches = make_method_matcher(methods)
    logdebug("weave_class (klass=%r, methods=%s, subclasses=%s, lazy=%s, owner=%s, name=%s, aliases=%s, bases=%s)",
             klass, methods, subclasses, lazy, owner, name, aliases, bases)

    if subclasses and hasattr(klass, '__subclasses__'):
        sub_targets = klass.__subclasses__()
        if sub_targets:
            logdebug("~ weaving subclasses: %s", sub_targets)
        for sub_class in sub_targets:
            if not issubclass(sub_class, Fabric):
                entanglement.merge(weave_class(sub_class, aspect,
                                               methods=methods, subclasses=subclasses, lazy=lazy, bag=bag))
    if lazy:
        def __init__(self, *args, **kwargs):
            super(SubClass, self).__init__(*args, **kwargs)
            for attr in dir(self):
                func = getattr(self, attr, None)
                if method_matches(attr) and attr not in wrappers and isroutine(func):
                    setattr(self, attr, _checked_apply(aspect, force_bind(func)).__get__(self, SubClass))

        wrappers = {
            '__init__': _checked_apply(aspect, __init__) if method_matches('__init__') else __init__
        }
        for attr, func in klass.__dict__.items():
            if method_matches(attr):
                if ismethoddescriptor(func):
                    wrappers[attr] = _rewrap_method(func, klass, aspect)

        logdebug(" * creating subclass with attributes %r", wrappers)
        name = name or klass.__name__
        SubClass = type(name, (klass, Fabric), wrappers)
        SubClass.__module__ = klass.__module__
        module = owner or __import__(klass.__module__)
        entanglement.merge(patch_module(module, name, SubClass, original=klass, aliases=aliases))
    else:
        original = {}
        for attr, func in klass.__dict__.items():
            if method_matches(attr):
                if isroutine(func):
                    logdebug("@ patching attribute %r (original: %r).", attr, func)
                    setattr(klass, attr, _rewrap_method(func, klass, aspect))
                else:
                    continue
                original[attr] = func
        entanglement.merge(lambda: deque((
            setattr(klass, attr, func) for attr, func in original.items()
        ), maxlen=0))
        if bases:
            super_original = set()
            for sklass in _find_super_classes(klass):
                if sklass is not object:
                    for attr, func in sklass.__dict__.items():
                        if method_matches(attr) and attr not in original and attr not in super_original:
                            if isroutine(func):
                                logdebug("@ patching attribute %r (from superclass: %s, original: %r).",
                                         attr, sklass.__name__, func)
                                setattr(klass, attr, _rewrap_method(func, sklass, aspect))
                            else:
                                continue
                            super_original.add(attr)
            entanglement.merge(lambda: deque((
                delattr(klass, attr) for attr in super_original
            ), maxlen=0))

    return entanglement


def _find_super_classes(klass):
    if hasattr(klass, '__mro__'):
        for k in klass.__mro__:
            yield k
    else:
        for base in klass.__bases__:
            yield base
            for k in _find_super_classes(base):
                yield k


def patch_module(module, name, replacement, original=UNSPECIFIED, aliases=True, location=None, **_bogus_options):
    """
    Low-level attribute patcher.

    :param module module: Object to patch.
    :param str name: Attribute to patch
    :param replacement: The replacement value.
    :param original: The original value (in case the object beeing patched uses descriptors or is plain weird).
    :param bool aliases: If ``True`` patch all the attributes that have the same original value.

    :returns: An :obj:`aspectlib.Rollback` object.
    """
    rollback = Rollback()
    seen = False
    original = getattr(module, name) if original is UNSPECIFIED else original
    location = module.__name__ if hasattr(module, '__name__') else type(module).__module__
    target = module.__name__ if hasattr(module, '__name__') else type(module).__name__
    try:
        replacement.__module__ = location
    except (TypeError, AttributeError):
        pass
    for alias in dir(module):
        logdebug("alias:%s (%s)", alias, name)
        if hasattr(module, alias):
            obj = getattr(module, alias)
            logdebug("- %s:%s (%s)", obj, original, obj is original)
            if obj is original:
                if aliases or alias == name:
                    logdebug("= saving %s on %s.%s ...", replacement, target, alias)
                    setattr(module, alias, replacement)
                    rollback.merge(lambda alias=alias: setattr(module, alias, original))
                if alias == name:
                    seen = True
            elif alias == name:
                if ismethod(obj):
                    logdebug("= saving %s on %s.%s ...", replacement, target, alias)
                    setattr(module, alias, replacement)
                    rollback.merge(lambda alias=alias: setattr(module, alias, original))
                    seen = True
                else:
                    raise AssertionError("%s.%s = %s is not %s." % (module, alias, obj, original))

    if not seen:
        warnings.warn('Setting %s.%s to %s. There was no previous definition, probably patching the wrong module.' % (
            target, name, replacement
        ))
        logdebug("= saving %s on %s.%s ...", replacement, target, name)
        setattr(module, name, replacement)
        rollback.merge(lambda: setattr(module, name, original))
    return rollback


def patch_module_function(module, target, aspect, force_name=None, bag=BrokenBag, **options):
    """
    Low-level patcher for one function from a specified module.

    .. warning:: You should not use this directly.

    :returns: An :obj:`aspectlib.Rollback` object.
    """
    logdebug("patch_module_function (module=%s, target=%s, aspect=%s, force_name=%s, **options=%s",
             module, target, aspect, force_name, options)
    name = force_name or target.__name__
    return patch_module(module, name, _checked_apply(aspect, target, module=module), original=target, **options)
