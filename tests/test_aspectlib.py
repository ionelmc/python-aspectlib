# encoding: utf8
from __future__ import print_function

import pytest
from pytest import raises

import aspectlib
from aspectlib.test import mock
from aspectlib.test import record


class Base(object):
    def meth(*_):
        return 'base'


Base2 = Base


class Sub(Base):
    pass


class Global(Base):
    pass


Global2 = Global


class MissingGlobal(Base):
    pass


AliasedGlobal = MissingGlobal
del MissingGlobal


def module_func():
    pass


def module_func2():
    pass


module_func3 = module_func2


class NormalTestClass(object):
    some = 'attribute'

    def __init__(self, foo=None):
        self.inst = self.foobar(foo)
        self.klass = self.class_foobar(foo)
        self.static = self.static_foobar(foo)
        self.other = 123

    def foobar(self, foo, bar=None):
        self.foo = foo
        self.bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.foo = foo
        cls.bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return bar or foo

    def only_in_base(self):
        return type(self).__name__


class NormalTestSubClass(NormalTestClass):
    def foobar(self, foo, bar=None):
        self.sub_foo = foo
        self.sub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.sub_foo = foo
        cls.sub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'sub' + (bar or foo)


class NormalTestSubSubClass(NormalTestSubClass):
    def foobar(self, foo, bar=None):
        self.subsub_foo = foo
        self.subsub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.subsub_foo = foo
        cls.subsub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'subsub' + (bar or foo)


class LegacyTestClass:
    some = 'attribute'

    def __init__(self, foo=None):
        self.inst = self.foobar(foo)
        self.klass = self.class_foobar(foo)
        self.static = self.static_foobar(foo)
        self.other = 123

    def foobar(self, foo, bar=None):
        self.foo = foo
        self.bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.foo = foo
        cls.bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return bar or foo

    def only_in_base(self):
        return self.__class__.__name__


class LegacyTestSubClass(LegacyTestClass):
    def foobar(self, foo, bar=None):
        self.sub_foo = foo
        self.sub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.sub_foo = foo
        cls.sub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'sub' + (bar or foo)


class LegacyTestSubSubClass(LegacyTestSubClass):
    def foobar(self, foo, bar=None):
        self.subsub_foo = foo
        self.subsub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.subsub_foo = foo
        cls.subsub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'subsub' + (bar or foo)


class SlotsTestClass(object):
    __slots__ = 'inst', 'klass', 'static', 'other', 'foo', 'bar'
    some = 'attribute'

    def __init__(self, foo=None):
        self.inst = self.foobar(foo)
        self.klass = self.class_foobar(foo)
        self.static = self.static_foobar(foo)
        self.other = 123

    def foobar(self, foo, bar=None):
        self.foo = foo
        self.bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.class_foo = foo
        cls.class_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return bar or foo


class SlotsTestSubClass(SlotsTestClass):
    __slots__ = 'inst', 'klass', 'static', 'other', 'foo', 'bar', 'sub_foo', 'sub_bar'

    def foobar(self, foo, bar=None):
        self.sub_foo = foo
        self.sub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.class_sub_foo = foo
        cls.class_sub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'sub' + (bar or foo)


class SlotsTestSubSubClass(SlotsTestSubClass):
    __slots__ = 'inst', 'klass', 'static', 'other', 'foo', 'bar', 'sub_foo', 'sub_bar', 'subsub_foo', 'subsub_bar'

    def foobar(self, foo, bar=None):
        self.subsub_foo = foo
        self.subsub_bar = bar

    @classmethod
    def class_foobar(cls, foo, bar=None):
        cls.class_subsub_foo = foo
        cls.class_subsub_bar = bar

    @staticmethod
    def static_foobar(foo, bar=None):
        return 'subsub' + (bar or foo)


def test_aspect_bad():
    @aspectlib.Aspect
    def aspect():
        yield

    def aspect_fail():
        return "crap"

    aspect.advising_function = aspect_fail

    @aspect
    def func():
        pass

    raises(aspectlib.ExpectedGenerator, func)


def test_aspect_gen_bind():
    called = []

    @aspectlib.Aspect(bind=True)
    def aspect(cutpoint):
        assert cutpoint.__name__ == 'func_g'
        yield
        called.append(True)

    @aspect
    def func_g():
        yield 1

    assert list(func_g()) == [1]
    assert called == [True]


def test_aspect_bind():
    called = []

    @aspectlib.Aspect(bind=True)
    def aspect(cutpoint):
        assert cutpoint.__name__ == 'func_g'
        yield
        called.append(True)

    @aspect
    def func_g():
        return 'foobar'

    assert func_g() == 'foobar'
    assert called == [True]


def test_aspect_bad_gen():
    @aspectlib.Aspect
    def aspect():
        yield

    def aspect_fail():
        return "crap"

    aspect.advising_function = aspect_fail

    @aspect
    def func():
        yield

    raises(aspectlib.ExpectedGenerator, list, func())


def test_aspect_bad_decorate():
    def aspect():
        return "crap"

    raises(aspectlib.ExpectedGeneratorFunction, aspectlib.Aspect, aspect)


def test_aspect_return():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Return

    @aspect
    def func():
        return 'stuff'

    assert func() is None


def test_aspect_return_value():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Return('stuff')

    @aspect
    def func():
        pass

    assert func() == 'stuff'


def test_aspect_raise():
    @aspectlib.Aspect
    def aspect():
        try:
            yield aspectlib.Proceed
        except ZeroDivisionError:
            pass
        else:
            raise AssertionError("didn't raise")

        yield aspectlib.Return('stuff')

    @aspect
    def func():
        1 / 0

    assert func() == 'stuff'


def test_aspect_raise_from_aspect():
    @aspectlib.Aspect
    def aspect():
        1 / 0
        yield

    @aspect
    def func():
        pass

    raises(ZeroDivisionError, func)


def test_aspect_return_but_call():
    calls = []

    @aspectlib.Aspect
    def aspect(_):
        assert 'first' == (yield aspectlib.Proceed)
        assert 'second' == (yield aspectlib.Proceed('second'))
        yield aspectlib.Return('stuff')

    @aspect
    def func(arg):
        calls.append(arg)
        return arg

    assert func('first') == 'stuff'
    assert calls == ['first', 'second']


def test_weave_func():
    with aspectlib.weave(module_func, mock('stuff')):
        assert module_func() == 'stuff'

    assert module_func() is None


def test_broken_aspect():
    raises(aspectlib.ExpectedAdvice, aspectlib.weave, None, None)


def test_weave_empty_target():
    raises(aspectlib.ExpectedAdvice, aspectlib.weave, (), None)


def test_weave_missing_global(cls=Global):
    global Global
    Global = 'crap'
    try:
        raises(AssertionError, aspectlib.weave, cls, mock('stuff'), lazy=True)
    finally:
        Global = cls


def test_weave_str_missing_target():
    raises(AttributeError, aspectlib.weave, 'test_pkg1.test_pkg2.target', mock('foobar'))


def test_weave_str_bad_target():
    raises(TypeError, aspectlib.weave, 'test_pkg1.test_pkg2.test_mod.a', mock('foobar'))


def test_weave_str_target():
    with aspectlib.weave('test_pkg1.test_pkg2.test_mod.target', mock('foobar')):
        from test_pkg1.test_pkg2.test_mod import target
        assert target() == 'foobar'

    from test_pkg1.test_pkg2.test_mod import target
    assert target() is None


def test_weave_str_class_target():
    with aspectlib.weave('test_pkg1.test_pkg2.test_mod.Stuff', mock('foobar')):
        from test_pkg1.test_pkg2.test_mod import Stuff
        assert Stuff().meth() == 'foobar'

    from test_pkg1.test_pkg2.test_mod import Stuff
    assert Stuff().meth() is None


def test_weave_str_class_meth_target():
    with aspectlib.weave('test_pkg1.test_pkg2.test_mod.Stuff.meth', mock('foobar')):
        from test_pkg1.test_pkg2.test_mod import Stuff
        assert Stuff().meth() == 'foobar'

    from test_pkg1.test_pkg2.test_mod import Stuff
    assert Stuff().meth() is None


def test_weave_old_style_method_no_warn_patch_module():
    calls = []
    with aspectlib.weave('warnings.warn', record(calls=calls)):
        with aspectlib.weave('test_aspectlib.LegacyTestClass.foobar', mock('stuff')):
            assert LegacyTestClass().foobar() == 'stuff'

    assert calls == []


def test_weave_wrong_module():
    calls = []
    with aspectlib.weave('warnings.warn', record(calls=calls)):
        aspectlib.weave(AliasedGlobal, mock('stuff'), lazy=True)
    assert calls == [
        (None,
         ("Setting test_aspectlib.MissingGlobal to <class 'test_aspectlib.MissingGlobal'>. "
          "There was no previous definition, probably patching the wrong module.",),
         {})
    ]


def test_weave_no_aliases():
    with aspectlib.weave(module_func2, mock('stuff'), aliases=False):
        assert module_func2() == 'stuff'
        assert module_func2 is not module_func3
        assert module_func3() is None

    assert module_func2() is None
    assert module_func3() is None
    assert module_func2 is module_func3


@pytest.mark.skipif('aspectlib.PY3')
def test_weave_class_meth_no_aliases():
    with aspectlib.weave(Global.meth, mock('stuff'), aliases=False, lazy=True):
        assert Global().meth() == 'stuff'
        assert Global2 is not Global
        assert Global2().meth() == 'base'

    assert Global().meth() == 'base'
    assert Global2 is Global
    assert Global2().meth() == 'base'


@pytest.mark.skipif('aspectlib.PY2')
def test_weave_class_meth_no_aliases_unsupported_on_py3():
    with aspectlib.weave(Global.meth, mock('stuff')):
        assert Global().meth() == 'stuff'
        assert Global2().meth() == 'stuff'

    assert Global().meth() == 'base'
    assert Global2().meth() == 'base'


def test_weave_class_no_aliases():
    with aspectlib.weave(Global, mock('stuff'), aliases=False, lazy=True):
        assert Global().meth() == 'stuff'
        assert Global2 is not Global
        assert Global2().meth() == 'base'

    assert Global().meth() == 'base'
    assert Global2 is Global
    assert Global2().meth() == 'base'


def test_weave_bad_args1():
    aspectlib.weave('warnings.warn', mock('stuff'), methods=['asdf'])


def test_weave_bad_args2():
    aspectlib.weave('warnings.warn', mock('stuff'), methods='(?!asdf)')


def test_weave_bad_args3():
    aspectlib.weave('warnings.warn', mock('stuff'), lazy=False)


def test_weave_bad_args4():
    aspectlib.weave('warnings.warn', mock('stuff'), subclasses=False)


def test_weave_bad_args5():
    raises(TypeError, aspectlib.weave, Sub, mock('stuff'), methods=False)


def test_weave_class_meth():
    @aspectlib.Aspect
    def aspect(self, *_):
        self.foo = 'bar'
        yield aspectlib.Return

    with aspectlib.weave(NormalTestClass.foobar, aspect):
        inst = NormalTestClass('stuff')
        assert inst.foo == 'bar'
        inst.foobar()

    inst = NormalTestClass('stuff')
    assert inst.foo == 'stuff'


def test_weave_instance_meth():
    @aspectlib.Aspect
    def aspect(self):
        self.foo = 'bar'
        yield aspectlib.Return

    inst = NormalTestClass()
    with aspectlib.weave(inst.foobar, aspect):
        inst.foobar()
        assert inst.foo == 'bar'

    inst.foobar('stuff')
    assert inst.foo == 'stuff'


@pytest.mark.skipif('aspectlib.PY2')
def test_weave_legacy_instance():
    @aspectlib.Aspect
    def aspect(self):
        self.foo = 'bar'
        yield aspectlib.Return

    inst = LegacyTestClass()
    with aspectlib.weave(inst, aspect):
        inst.foobar()
        assert inst.foo == 'bar'

    inst.foobar('stuff')
    assert inst.foo == 'stuff'


def test_weave_instance():
    @aspectlib.Aspect
    def aspect(self):
        self.foo = 'bar'
        yield aspectlib.Return

    inst = NormalTestClass()
    with aspectlib.weave(inst, aspect):
        inst.foobar()
        assert inst.foo == 'bar'

    inst.foobar('stuff')
    assert inst.foo == 'stuff'


def test_weave_subclass_meth_from_baseclass():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        result = yield
        history.append(args + (result,))
        yield aspectlib.Return('bar-' + result)

    with aspectlib.weave(NormalTestSubClass.only_in_base, aspect):
        inst = NormalTestSubClass('stuff')
        assert inst.only_in_base() == 'bar-NormalTestSubClass'
        assert history == [
            (inst, 'NormalTestSubClass'),
        ]

    inst = NormalTestSubClass('stuff')
    assert inst.only_in_base() == 'NormalTestSubClass'


def test_weave_subclass_meth_from_baseclass_2_level():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        result = yield
        history.append(args + (result,))
        yield aspectlib.Return('bar-' + result)

    with aspectlib.weave(NormalTestSubSubClass.only_in_base, aspect):
        inst = NormalTestSubSubClass('stuff')
        assert inst.only_in_base() == 'bar-NormalTestSubSubClass'
        assert history == [
            (inst, 'NormalTestSubSubClass'),
        ]

    inst = NormalTestSubSubClass('stuff')
    assert inst.only_in_base() == 'NormalTestSubSubClass'


def test_weave_legacy_subclass_meth_from_baseclass():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        result = yield
        history.append(args + (result,))
        yield aspectlib.Return('bar-' + result)

    with aspectlib.weave(LegacyTestSubClass.only_in_base, aspect):
        inst = LegacyTestSubClass('stuff')
        assert inst.only_in_base() == 'bar-LegacyTestSubClass'
        assert history == [
            (inst, 'LegacyTestSubClass'),
        ]

    inst = LegacyTestSubClass('stuff')
    assert inst.only_in_base() == 'LegacyTestSubClass'


def test_weave_legacy_subclass_meth_from_baseclass_2_level():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        result = yield
        history.append(args + (result,))
        yield aspectlib.Return('bar-' + result)

    with aspectlib.weave(LegacyTestSubSubClass.only_in_base, aspect):
        inst = LegacyTestSubSubClass('stuff')
        assert inst.only_in_base() == 'bar-LegacyTestSubSubClass'
        assert history == [
            (inst, 'LegacyTestSubSubClass'),
        ]

    inst = LegacyTestSubSubClass('stuff')
    assert inst.only_in_base() == 'LegacyTestSubSubClass'


def test_weave_class():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        args += ':)',
        yield aspectlib.Proceed(*args)
        yield aspectlib.Return('bar')

    inst = NormalTestClass()

    with aspectlib.weave(NormalTestClass, aspect):
        inst = NormalTestClass('stuff')
        assert inst.foo == 'stuff'
        assert inst.bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert NormalTestClass.foo == 'stuff'
        assert NormalTestClass.bar == ':)'
        assert NormalTestClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (NormalTestClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

        inst = NormalTestSubClass('stuff')
        assert inst.sub_foo == 'stuff'
        assert inst.sub_bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert NormalTestSubClass.sub_foo == 'stuff'
        assert NormalTestSubClass.sub_bar == ':)'
        assert NormalTestSubClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (NormalTestSubClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

        inst = NormalTestSubSubClass('stuff')
        assert inst.subsub_foo == 'stuff'
        assert inst.subsub_bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert NormalTestSubSubClass.subsub_foo == 'stuff'
        assert NormalTestSubSubClass.subsub_bar == ':)'
        assert NormalTestSubSubClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (NormalTestSubSubClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

    inst = NormalTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert NormalTestClass.foo == 'stuff'
    assert NormalTestClass.bar is None
    assert NormalTestClass.static_foobar('stuff') == 'stuff'

    inst = NormalTestSubClass('stuff')
    assert inst.sub_foo == 'stuff'
    assert inst.sub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'substuff'
    assert NormalTestSubClass.sub_foo == 'stuff'
    assert NormalTestSubClass.sub_bar is None
    assert NormalTestSubClass.static_foobar('stuff') == 'substuff'

    inst = NormalTestSubSubClass('stuff')
    assert inst.subsub_foo == 'stuff'
    assert inst.subsub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'subsubstuff'
    assert NormalTestSubSubClass.subsub_foo == 'stuff'
    assert NormalTestSubSubClass.subsub_bar is None
    assert NormalTestSubSubClass.static_foobar('stuff') == 'subsubstuff'

    assert history == []


def test_weave_class_slots():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        args += ':)',
        yield aspectlib.Proceed(*args)
        yield aspectlib.Return('bar')

    inst = SlotsTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert SlotsTestClass.class_foo == 'stuff'
    assert SlotsTestClass.class_bar is None
    assert SlotsTestClass.static_foobar('stuff') == 'stuff'

    inst = SlotsTestClass()
    with aspectlib.weave(SlotsTestClass, aspect):
        inst = SlotsTestClass('stuff')
        assert inst.foo == 'stuff'
        assert inst.bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert SlotsTestClass.class_foo == 'stuff'
        assert SlotsTestClass.class_bar == ':)'
        assert SlotsTestClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (SlotsTestClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

        inst = SlotsTestSubClass('stuff')
        assert inst.sub_foo == 'stuff'
        assert inst.sub_bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert SlotsTestSubClass.class_sub_foo == 'stuff'
        assert SlotsTestSubClass.class_sub_bar == ':)'
        assert SlotsTestSubClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (SlotsTestSubClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

        inst = SlotsTestSubSubClass('stuff')
        assert inst.subsub_foo == 'stuff'
        assert inst.subsub_bar == ':)'
        assert inst.inst == 'bar'
        assert inst.klass == 'bar'
        assert inst.static == 'bar'
        assert SlotsTestSubSubClass.class_subsub_foo == 'stuff'
        assert SlotsTestSubSubClass.class_subsub_bar == ':)'
        assert SlotsTestSubSubClass.static_foobar('stuff') == 'bar'
        assert history == [
            (inst, 'stuff'),
            (SlotsTestSubSubClass, 'stuff'),
            ('stuff',),
            ('stuff',),
        ]
        del history[:]

    inst = SlotsTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert SlotsTestClass.class_foo == 'stuff'
    assert SlotsTestClass.class_bar is None
    assert SlotsTestClass.static_foobar('stuff') == 'stuff'

    inst = SlotsTestSubClass('stuff')
    assert inst.sub_foo == 'stuff'
    assert inst.sub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'substuff'
    assert SlotsTestSubClass.class_sub_foo == 'stuff'
    assert SlotsTestSubClass.class_sub_bar is None
    assert SlotsTestSubClass.static_foobar('stuff') == 'substuff'

    inst = SlotsTestSubSubClass('stuff')
    assert inst.subsub_foo == 'stuff'
    assert inst.subsub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'subsubstuff'
    assert SlotsTestSubSubClass.class_subsub_foo == 'stuff'
    assert SlotsTestSubSubClass.class_subsub_bar is None
    assert SlotsTestSubSubClass.static_foobar('stuff') == 'subsubstuff'

    assert history == []


def test_weave_class_on_init():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        args += ':)',
        yield aspectlib.Proceed(*args)
        yield aspectlib.Return('bar')

    inst = SlotsTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert SlotsTestClass.class_foo == 'stuff'
    assert SlotsTestClass.class_bar is None
    assert SlotsTestClass.static_foobar('stuff') == 'stuff'

    inst = SlotsTestClass()
    with aspectlib.weave(SlotsTestClass, aspect, lazy=True):
        inst = SlotsTestClass('stuff')
        assert inst.foo == 'stuff'
        assert inst.bar is None
        assert inst.inst is None
        assert inst.foobar('bluff') == 'bar'
        assert inst.foo == 'bluff'
        assert inst.bar == ':)'
        assert inst.class_foobar('bluff') == 'bar'
        assert SlotsTestClass.class_foo == 'bluff'
        assert SlotsTestClass.class_bar == ':)'
        assert SlotsTestClass.static_foobar('stuff') == 'bar'

        inst = SlotsTestSubClass('stuff')
        assert inst.sub_foo == 'stuff'
        assert inst.sub_bar is None
        assert inst.inst is None
        assert inst.foobar('bluff') == 'bar'
        assert inst.sub_foo == 'bluff'
        assert inst.sub_bar == ':)'
        assert inst.class_foobar('bluff') == 'bar'
        assert SlotsTestSubClass.class_sub_foo == 'bluff'
        assert SlotsTestSubClass.class_sub_bar == ':)'
        assert SlotsTestSubClass.static_foobar('stuff') == 'bar'

        inst = SlotsTestSubSubClass('stuff')
        assert inst.subsub_foo == 'stuff'
        assert inst.subsub_bar is None
        assert inst.inst is None
        assert inst.foobar('bluff') == 'bar'
        assert inst.subsub_foo == 'bluff'
        assert inst.subsub_bar == ':)'
        assert inst.class_foobar('bluff') == 'bar'
        assert SlotsTestSubSubClass.class_subsub_foo == 'bluff'
        assert SlotsTestSubSubClass.class_subsub_bar == ':)'
        assert SlotsTestSubSubClass.static_foobar('stuff') == 'bar'

    del history[:]

    inst = SlotsTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert SlotsTestClass.class_foo == 'stuff'
    assert SlotsTestClass.class_bar is None
    assert SlotsTestClass.static_foobar('stuff') == 'stuff'

    inst = SlotsTestSubClass('stuff')
    assert inst.sub_foo == 'stuff'
    assert inst.sub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'substuff'
    assert SlotsTestSubClass.class_sub_foo == 'stuff'
    assert SlotsTestSubClass.class_sub_bar is None
    assert SlotsTestSubClass.static_foobar('stuff') == 'substuff'

    inst = SlotsTestSubSubClass('stuff')
    assert inst.subsub_foo == 'stuff'
    assert inst.subsub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'subsubstuff'
    assert SlotsTestSubSubClass.class_subsub_foo == 'stuff'
    assert SlotsTestSubSubClass.class_subsub_bar is None
    assert SlotsTestSubSubClass.static_foobar('stuff') == 'subsubstuff'

    assert history == []


def test_weave_class_old_style():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        args += ':)',
        yield aspectlib.Proceed(*args)
        yield aspectlib.Return('bar')

    inst = LegacyTestClass()

    with aspectlib.weave(LegacyTestClass, aspect, subclasses=False):
        with aspectlib.weave(LegacyTestSubClass, aspect, subclasses=False):
            with aspectlib.weave(LegacyTestSubSubClass, aspect, subclasses=False):
                inst = LegacyTestClass('stuff')
                assert inst.foo == 'stuff'
                assert inst.bar == ':)'
                assert inst.inst == 'bar'
                assert inst.klass == 'bar'
                assert inst.static == 'bar'
                assert LegacyTestClass.foo == 'stuff'
                assert LegacyTestClass.bar == ':)'
                assert LegacyTestClass.static_foobar('stuff') == 'bar'
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestClass, 'stuff'),
                    ('stuff',),
                    ('stuff',),
                ]
                del history[:]

                inst = LegacyTestSubClass('stuff')
                assert inst.sub_foo == 'stuff'
                assert inst.sub_bar == ':)'
                assert inst.inst == 'bar'
                assert inst.klass == 'bar'
                assert inst.static == 'bar'
                assert LegacyTestSubClass.sub_foo == 'stuff'
                assert LegacyTestSubClass.sub_bar == ':)'
                assert LegacyTestSubClass.static_foobar('stuff') == 'bar'
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestSubClass, 'stuff'),
                    ('stuff',),
                    ('stuff',),
                ]
                del history[:]

                inst = LegacyTestSubSubClass('stuff')
                assert inst.subsub_foo == 'stuff'
                assert inst.subsub_bar == ':)'
                assert inst.inst == 'bar'
                assert inst.klass == 'bar'
                assert inst.static == 'bar'
                assert LegacyTestSubSubClass.subsub_foo == 'stuff'
                assert LegacyTestSubSubClass.subsub_bar == ':)'
                assert LegacyTestSubSubClass.static_foobar('stuff') == 'bar'
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestSubSubClass, 'stuff'),
                    ('stuff',),
                    ('stuff',),
                ]
                del history[:]

    inst = LegacyTestClass('stuff')
    assert inst.foo == 'stuff'
    assert inst.bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'stuff'
    assert LegacyTestClass.foo == 'stuff'
    assert LegacyTestClass.bar is None
    assert LegacyTestClass.static_foobar('stuff') == 'stuff'

    inst = LegacyTestSubClass('stuff')
    assert inst.sub_foo == 'stuff'
    assert inst.sub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'substuff'
    assert LegacyTestSubClass.sub_foo == 'stuff'
    assert LegacyTestSubClass.sub_bar is None
    assert LegacyTestSubClass.static_foobar('stuff') == 'substuff'

    inst = LegacyTestSubSubClass('stuff')
    assert inst.subsub_foo == 'stuff'
    assert inst.subsub_bar is None
    assert inst.inst is None
    assert inst.klass is None
    assert inst.static == 'subsubstuff'
    assert LegacyTestSubSubClass.subsub_foo == 'stuff'
    assert LegacyTestSubSubClass.subsub_bar is None
    assert LegacyTestSubSubClass.static_foobar('stuff') == 'subsubstuff'

    assert history == []


def test_weave_class_all_magic():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        yield aspectlib.Proceed

    inst = NormalTestClass()

    with aspectlib.weave(NormalTestClass, aspect, methods=aspectlib.ALL_METHODS):
        inst = NormalTestClass('stuff')
        assert history == [
            (inst, 'stuff'),
            (inst, 'stuff'),
            (NormalTestClass, 'stuff'),
            ('stuff',),
        ]
        del history[:]

        inst = NormalTestSubClass('stuff')
        assert history == [
            (inst, 'stuff'),
            (inst, 'stuff'),
            (NormalTestSubClass, 'stuff'),
            ('stuff',),
        ]
        del history[:]

        inst = NormalTestSubSubClass('stuff')
        assert history == [
            (inst, 'stuff'),
            (inst, 'stuff'),
            (NormalTestSubSubClass, 'stuff'),
            ('stuff',),
        ]
        del history[:]

    inst = NormalTestClass('stuff')
    inst = NormalTestSubClass('stuff')
    inst = NormalTestSubSubClass('stuff')

    assert history == []


def test_weave_class_old_style_all_magic():
    history = []

    @aspectlib.Aspect
    def aspect(*args):
        history.append(args)
        yield aspectlib.Proceed

    inst = LegacyTestClass()

    with aspectlib.weave(LegacyTestClass, aspect, subclasses=False):
        with aspectlib.weave(LegacyTestSubClass, aspect, subclasses=False):
            with aspectlib.weave(LegacyTestSubSubClass, aspect, subclasses=False):
                inst = LegacyTestClass('stuff')
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestClass, 'stuff'),
                    ('stuff',),
                ]
                del history[:]

                inst = LegacyTestSubClass('stuff')
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestSubClass, 'stuff'),
                    ('stuff',),
                ]
                del history[:]

                inst = LegacyTestSubSubClass('stuff')
                assert history == [
                    (inst, 'stuff'),
                    (LegacyTestSubSubClass, 'stuff'),
                    ('stuff',),
                ]
                del history[:]

    inst = LegacyTestClass('stuff')
    inst = LegacyTestSubClass('stuff')
    inst = LegacyTestSubSubClass('stuff')

    assert history == []


def test_just_proceed():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        return 'stuff'

    assert func() == 'stuff'


def test_just_proceed_with_error():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        1 / 0

    raises(ZeroDivisionError, func)


def test_weave_unknown():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    raises(aspectlib.UnsupportedType, aspectlib.weave, 1, aspect)


def test_weave_unimportable():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    raises(ImportError, aspectlib.weave, "asdf1.qwer2", aspect)


def test_weave_subclass(Bub=Sub):
    with aspectlib.weave(Sub, mock('foobar'), lazy=True):
        assert Sub().meth() == 'foobar'
        assert Bub().meth() == 'base'
    assert Sub().meth() == 'base'
    assert Bub is Sub


def test_weave_subclass_meth_manual():
    with aspectlib.weave(Sub, mock('foobar'), lazy=True, methods=['meth']):
        assert Sub().meth() == 'foobar'

    assert Sub().meth() == 'base'


@pytest.mark.skipif('aspectlib.PY3')
def test_weave_subclass_meth_auto():
    with aspectlib.weave(Sub.meth, mock('foobar'), lazy=True):
        assert Sub().meth() == 'foobar'

    assert Sub().meth() == 'base'


@pytest.mark.skipif('aspectlib.PY2')
def test_weave_subclass_meth_auto2():
    with aspectlib.weave(Sub.meth, mock('foobar')):
        assert Sub().meth() == 'foobar'

    assert Sub().meth() == 'base'


def test_weave_multiple():
    with aspectlib.weave((module_func, module_func2), mock('foobar')):
        assert module_func() == 'foobar'
        assert module_func2() == 'foobar'

    assert module_func() is None
    assert module_func2() is None


def test_unspecified_str():
    assert repr(aspectlib.UNSPECIFIED) == 'UNSPECIFIED'


def test_sentinel():
    assert repr(aspectlib.Sentinel('STUFF', "Means it's some stuff")) == "STUFF: Means it's some stuff"


def _internal():
    pass


if aspectlib.PY3:
    exec(u"""# encoding: utf8

def ăbc():
    pass

def test_ăbc():
    with aspectlib.weave('test_aspectlib.ăbc', mock('stuff')):
        assert ăbc() == 'stuff'
""")
else:
    def test_py2_invalid_unicode_in_string_target():
        raises(SyntaxError, aspectlib.weave, 'os.ăa', mock(None))
        raises(SyntaxError, aspectlib.weave, u'os.ăa', mock(None))
        raises(SyntaxError, aspectlib.weave, 'os.aă', mock(None))
        raises(SyntaxError, aspectlib.weave, u'os.aă', mock(None))


def test_invalid_string_target():
    raises(SyntaxError, aspectlib.weave, 'inva lid', mock(None))
    raises(SyntaxError, aspectlib.weave, 'os.inva lid', mock(None))
    raises(SyntaxError, aspectlib.weave, 'os.2invalid', mock(None))
    raises(SyntaxError, aspectlib.weave, 'os.some,junk', mock(None))
    raises(SyntaxError, aspectlib.weave, 'os.some?junk', mock(None))
    raises(SyntaxError, aspectlib.weave, 'os.some*junk', mock(None))

    with aspectlib.weave('test_aspectlib._internal', mock('stuff')):
        assert _internal() == 'stuff'


def test_list_of_aspects():
    with aspectlib.weave(module_func, [mock('foobar'), record]):
        assert module_func(1, 2, 3) == 'foobar'
        assert module_func.calls == [(None, (1, 2, 3), {})]

    with aspectlib.weave(module_func, [mock('foobar', call=True), record]):
        raises(TypeError, module_func, 1, 2, 3)
        assert module_func.calls == [(None, (1, 2, 3), {})]


def test_list_of_invalid_aspects():
    raises(AssertionError, aspectlib.weave, module_func, [lambda func: None])
    raises(TypeError, aspectlib.weave, module_func, [lambda: None])
    raises(aspectlib.ExpectedAdvice, aspectlib.weave, module_func, [None])
    raises(aspectlib.ExpectedAdvice, aspectlib.weave, module_func, ['foobar'])


def test_aspect_on_func():
    hist = []

    @aspectlib.Aspect
    def aspect():
        try:
            hist.append('before')
            hist.append((yield aspectlib.Proceed))
            hist.append('after')
        except Exception:
            hist.append('error')
        finally:
            hist.append('finally')
        try:
            hist.append((yield aspectlib.Return('squelched')))
        except GeneratorExit:
            hist.append('closed')
            raise
        else:
            hist.append('consumed')

    @aspect
    def func():
        raise RuntimeError()

    assert func() == 'squelched'
    assert hist == ['before', 'error', 'finally', 'closed']


def test_aspect_on_func_invalid_advice():
    hist = []

    @aspectlib.Aspect
    def aspect():
        yield "stuff"

    @aspect
    def func():
        raise RuntimeError()

    raises(aspectlib.UnacceptableAdvice, func)


def test_aspect_on_generator_func():
    hist = []

    @aspectlib.Aspect
    def aspect():
        try:
            hist.append('before')
            yield aspectlib.Proceed
            hist.append('after')
        except Exception:
            hist.append('error')
        finally:
            hist.append('finally')
        try:
            hist.append((yield aspectlib.Return))
        except GeneratorExit:
            hist.append('closed')
            raise
        else:
            hist.append('consumed')
        hist.append('bad-suffix')

    @aspect
    def func():
        for i in range(3):
            yield i
        raise RuntimeError()

    assert list(func()) == [0, 1, 2]
    print(hist)
    assert hist == ['before', 'error', 'finally', 'closed']


def test_aspect_on_generator_func_bad_advice():
    @aspectlib.Aspect
    def aspect():
        yield 'crappo'

    @aspect
    def func():
        for i in range(3):
            yield i
        raise RuntimeError()

    raises(aspectlib.UnacceptableAdvice, list, func())


def test_aspect_on_generator_different_args():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed('something')

    @aspect
    def func(arg=None):
        yield arg

    assert list(func()) == ['something']


def test_aspect_on_generator_raise_stopiteration():
    result = []

    @aspectlib.Aspect
    def aspect():
        val = yield aspectlib.Proceed
        result.append(val)

    @aspect
    def func():
        raise StopIteration('something')
        yield

    assert list(func()) == []
    assert result == ['something']


def test_aspect_on_generator_close():
    excs = []

    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        try:
            yield 'something'
        except BaseException as exc:
            excs.append(type(exc))

    assert list(func()) == ['something']
    assert excs == []

    gen = func()
    next(gen)
    gen.close()
    del gen
    assert excs == [GeneratorExit]


def test_aspect_on_generator_throw():
    excs = []

    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        try:
            yield 'something'
        except BaseException as exc:
            excs.append(type(exc))
        yield 'lastthing'

    assert list(func()) == ['something', 'lastthing']
    assert excs == []

    gen = func()
    print(next(gen))
    gen.throw(RuntimeError)
    assert excs == [RuntimeError]


def test_aspect_on_generator_throw_exhaust():
    excs = []

    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        try:
            yield 'something'
        except BaseException as exc:
            excs.append(type(exc))

    assert list(func()) == ['something']
    assert excs == []

    gen = func()
    print(next(gen))
    raises(StopIteration, gen.throw, RuntimeError)
    assert excs == [RuntimeError]


def test_aspect_on_generator_send_in_aspect():
    values = []

    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    @aspect
    def func():
        values.append((yield 'something'))
        yield
        values.append((yield))
        yield

    gen = func()
    gen.send(None)
    gen.send(1)
    gen.send(2)
    gen.send(3)

    assert values == [1, 3]


def test_aspect_on_generator_result_from_aspect():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed
        yield aspectlib.Return('result')

    @aspect
    def func():
        yield 'something'

    gen = func()
    try:
        while 1:
            next(gen)
    except StopIteration as exc:
        assert exc.args == ('result',)
    else:
        raise AssertionError("did not raise StopIteration")


def test_aspect_on_generator_result():
    result = []

    @aspectlib.Aspect
    def aspect():
        result.append((yield aspectlib.Proceed))

    @aspect
    def func():
        yield 'something'
        raise StopIteration('value')

    assert list(func()) == ['something']
    assert result == ['value']


def test_aspect_on_coroutine():
    hist = []

    @aspectlib.Aspect
    def aspect():
        try:
            hist.append('before')
            hist.append((yield aspectlib.Proceed))
            hist.append('after')
        except Exception:
            hist.append('error')
        finally:
            hist.append('finally')
        try:
            hist.append((yield aspectlib.Return))
        except GeneratorExit:
            hist.append('closed')
            raise
        else:
            hist.append('consumed')
        hist.append('bad-suffix')

    @aspect
    def func():
        val = 99
        for _ in range(3):
            print("YIELD", val + 1)
            val = yield val + 1
            print("GOT", val)
        raise StopIteration("the-return-value")

    gen = func()
    data = []
    try:
        for i in [None, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]:
            data.append(gen.send(i))
    except StopIteration:
        data.append('done')
    print(data)
    assert data == [100, 1, 2, 'done'], hist
    print(hist)
    assert hist == ['before', 'the-return-value', 'after', 'finally', 'closed']


def test_weave_module(strmod=None):
    calls = []
    from test_pkg1.test_pkg2 import test_mod
    with aspectlib.weave(strmod or test_mod, record(calls=calls, extended=True)):
        test_mod.target()
        obj = test_mod.Stuff()
        obj.meth()
    assert calls == [
        (None, 'test_pkg1.test_pkg2.test_mod.target', (), {}),
        (obj, 'test_pkg1.test_pkg2.test_mod.meth', (), {})
    ]


def test_weave_module_as_str():
    test_weave_module("test_pkg1.test_pkg2.test_mod")


def test_aspect_chain_on_generator():
    @aspectlib.Aspect
    def foo(arg):
        result = yield aspectlib.Proceed(arg + 1)
        yield aspectlib.Return(result - 1)

    @foo
    @foo
    @foo
    def func(a):
        assert a == 3
        raise StopIteration(a)
        yield

    gen = func(0)
    result = pytest.raises(StopIteration, gen.__next__ if hasattr(gen, '__next__') else gen.next)
    assert result.value.args == (0,)


def test_aspect_chain_on_generator_no_return():
    @aspectlib.Aspect
    def foo(arg):
        result = yield aspectlib.Proceed(arg + 1)
        yield aspectlib.Return(result)

    @foo
    @foo
    @foo
    def func(a):
        assert a == 3
        yield

    gen = func(0)
    if hasattr(gen, '__next__'):
        assert gen.__next__() is None
        result = pytest.raises(StopIteration, gen.__next__)
    else:
        assert gen.next() is None
        result = pytest.raises(StopIteration, gen.next)
    assert result.value.args == (None,)


def test_aspect_chain_on_generator_no_return_advice():
    @aspectlib.Aspect
    def foo(arg):
        yield aspectlib.Proceed(arg + 1)

    @foo
    @foo
    @foo
    def func(a):
        assert a == 3
        raise StopIteration(a)
        yield

    gen = func(0)
    if hasattr(gen, '__next__'):
        result = pytest.raises(StopIteration, gen.__next__)
    else:
        result = pytest.raises(StopIteration, gen.next)
    assert result.value.args == (3,)
