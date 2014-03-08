from __future__ import print_function

import pytest
from pytest import raises

import aspectlib
from aspectlib.test import mock
from aspectlib.test import record



class Base(object):
    def meth(*_):
        return 'base'


class Sub(Base):
    pass


class Global(Base):
    pass


class MissingGlobal(Base):
    pass

AliasedGlobal = MissingGlobal
del MissingGlobal


def module_func():
    pass


def module_func2():
    pass


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
        return "crap"

    @aspect
    def func():
        pass

    raises(RuntimeError, func)


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
        1/0

    assert func() == 'stuff'


def test_aspect_raise_from_aspect():
    @aspectlib.Aspect
    def aspect():
        1/0

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
    assert calls, ['first' == 'second']


def test_weave_func():
    with aspectlib.weave(module_func, mock('stuff')):
        assert module_func() == 'stuff'

    assert module_func() is None


def test_broken_aspect():
    raises(AssertionError, aspectlib.weave, None, None)


def test_weave_empty_target():
    raises(AssertionError, aspectlib.weave, (), None)


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
    raises(RuntimeError, aspectlib.weave, 'test_pkg1.test_pkg2.test_mod.a', mock('foobar'))


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


def test_weave_wrong_module():
    calls = []
    with aspectlib.weave('warnings.warn', record(history=calls)):
        aspectlib.weave(AliasedGlobal, mock('stuff'), lazy=True)
    assert calls == [
        (None,
         ("Setting test_aspectlib.MissingGlobal to <class 'test_aspectlib.MissingGlobal'>. "
          "There was no previous definition, probably patching the wrong module.",),
         {})
    ]


def test_weave_bad_args1():
    raises(TypeError, aspectlib.weave, 'warnings.warn', mock('stuff'), methods=['asdf'])


def test_weave_bad_args2():
    raises(TypeError, aspectlib.weave, 'warnings.warn', mock('stuff'), methods='(?!asdf)')


@pytest.mark.xfail(reason="hmmm")
def test_weave_bad_args3():
    raises(TypeError, aspectlib.weave, 'warnings.warn', mock('stuff'), lazy=False)


def test_weave_bad_args4():
    raises(TypeError, aspectlib.weave, 'warnings.warn', mock('stuff'), subclasses=False)


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
        1/0

    raises(ZeroDivisionError, func)


def test_weave_unknown():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    raises(RuntimeError, aspectlib.weave, 1, aspect)


def test_weave_unimportable():
    @aspectlib.Aspect
    def aspect():
        yield aspectlib.Proceed

    raises(ImportError, aspectlib.weave, "1.2", aspect)


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
