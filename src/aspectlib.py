from types import GeneratorType, FunctionType, ModuleType, MethodType, UnboundMethodType, ClassType, InstanceType
import sys


class proceed(object):  # pylint: disable=C0103
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class return_(object):  # pylint: disable=C0103
    def __init__(self, value):
        self.value = value


class aspect(object):  # pylint: disable=C0103
    def __init__(self, advise_function):
        assert callable(advise_function)
        self.advise_function = advise_function

    def decorate(self, cutpoint_function):
        def advice_wrapper(*args, **kwargs):
            advisor = self.advise_function(*args, **kwargs)
            if not isinstance(advisor, GeneratorType):
                raise RuntimeError("advise_function %s did not return a generator." % self.advise_function)
            advice = advisor.send(None)
            while True:
                if advice is proceed or isinstance(advice, proceed):
                    if advice is not proceed:
                        args = advice.args
                        kwargs = advice.kwargs
                    try:
                        advice = advisor.send(cutpoint_function(*args, **kwargs))
                    except Exception:
                        advice = advisor.throw(*sys.exc_info())
                elif advice is return_:
                    return
                elif isinstance(advice, return_):
                    return advice.value
        return advice_wrapper


class Weaver(object):
    pass


class Entanglement(object):  # pylint: disable=C0103
    def __init__(self, rollback):
        self.rollback = rollback

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.rollback()


weaver_registry = {
    FunctionType, ModuleType, MethodType, UnboundMethodType, ClassType, InstanceType
}


def weave(target, aspect_or_factory, *factory_args, **factory_kwargs):
    if isinstance(aspect_or_factory, aspect):
        aspect_inst = aspect_or_factory
    else:
        aspect_inst = aspect_or_factory(*factory_args, **factory_kwargs)
    assert isinstance(aspect_inst, aspect), '%s did not return an Aspect instance, it return %s.' % (aspect_or_factory, aspect)

    if isinstance(target, FunctionType):
        mod = __import__(target.__module__)
        name = target.__name__
        assert getattr(mod, name) is target
        setattr(mod, name, aspect_inst.decorate(target))
        return Entanglement(lambda: setattr(mod, name, target))
    elif isinstance(target, UnboundMethodType):
        klass = target.im_class
        name = target.__name__
        func = klass.__dict__[name]
        setattr(klass, name, aspect_inst.decorate(target))
        return Entanglement(lambda: setattr(klass, name, func))
    elif isinstance(target, ClassType):
        pass

