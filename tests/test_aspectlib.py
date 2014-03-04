from __future__ import print_function

import unittest
import aspectlib

from aspectlib.test import mock


class Base(object):
    def meth(*_):
        return 'base'


class Sub(Base):
    pass


class AOPTestCase(unittest.TestCase):

    def test_aspect_bad(self):
        @aspectlib.Aspect
        def aspect(*args, **kwargs):
            return "crap"

        @aspect
        def func():
            pass

        self.assertRaises(RuntimeError, func)

    def test_aspect_return(self):
        @aspectlib.Aspect
        def aspect(*args, **kwargs):
            yield aspectlib.Return

        @aspect
        def func():
            return 'stuff'

        self.assertEqual(func(), None)

    def test_aspect_return_value(self):
        @aspectlib.Aspect
        def aspect(*args, **kwargs):
            yield aspectlib.Return('stuff')

        @aspect
        def func():
            pass

        self.assertEqual(func(), 'stuff')

    def test_aspect_raise(self):
        @aspectlib.Aspect
        def aspect(*args, **kwargs):
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

        self.assertEqual(func(), 'stuff')

    def test_aspect_raise_from_aspect(self):
        @aspectlib.Aspect
        def aspect(*args, **kwargs):
            1/0

        @aspect
        def func():
            pass

        self.assertRaises(ZeroDivisionError, func)

    def test_aspect_return_but_call(self):
        calls = []

        @aspectlib.Aspect
        def aspect(arg):
            assert 'first' == (yield aspectlib.Proceed)
            assert 'second' == (yield aspectlib.Proceed('second'))
            yield aspectlib.Return('stuff')

        @aspect
        def func(arg):
            calls.append(arg)
            return arg

        self.assertEqual(func('first'), 'stuff')
        self.assertEqual(calls, ['first', 'second'])

    def test_weave_func(self):
        with aspectlib.weave(module_func, mock(returns='stuff')):
            self.assertEqual(module_func(), 'stuff')

        self.assertEqual(module_func(), None)

    def test_weave_class_meth(self):
        @aspectlib.Aspect
        def aspect(self, *_):
            self.foo = 'bar'
            yield aspectlib.Return

        with aspectlib.weave(TestClass.foobar, aspect):
            inst = TestClass('stuff')
            self.assertEqual(inst.foo, 'bar')
            inst.foobar()

        inst = TestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')

    def test_weave_instance_meth(self):
        @aspectlib.Aspect
        def aspect(self):
            self.foo = 'bar'
            yield aspectlib.Return

        inst = TestClass()
        with aspectlib.weave(inst.foobar, aspect):
            inst.foobar()
            self.assertEqual(inst.foo, 'bar')

        inst.foobar('stuff')
        self.assertEqual(inst.foo, 'stuff')

    def test_weave_class(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.Proceed(*args)
            yield aspectlib.Return('bar')

        inst = TestClass()

        with aspectlib.weave(TestClass, aspect):
            inst = TestClass('stuff')
            self.assertEqual(inst.foo, 'stuff')
            self.assertEqual(inst.bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(TestClass.foo, 'stuff')
            self.assertEqual(TestClass.bar, ':)')
            self.assertEqual(TestClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (TestClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubClass('stuff')
            self.assertEqual(inst.sub_foo, 'stuff')
            self.assertEqual(inst.sub_bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(TestSubClass.sub_foo, 'stuff')
            self.assertEqual(TestSubClass.sub_bar, ':)')
            self.assertEqual(TestSubClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (TestSubClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubSubClass('stuff')
            self.assertEqual(inst.subsub_foo, 'stuff')
            self.assertEqual(inst.subsub_bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(TestSubSubClass.subsub_foo, 'stuff')
            self.assertEqual(TestSubSubClass.subsub_bar, ':)')
            self.assertEqual(TestSubSubClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (TestSubSubClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

        inst = TestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(TestClass.foo, 'stuff')
        self.assertEqual(TestClass.bar, None)
        self.assertEqual(TestClass.static_foobar('stuff'), 'stuff')

        inst = TestSubClass('stuff')
        self.assertEqual(inst.sub_foo, 'stuff')
        self.assertEqual(inst.sub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'substuff')
        self.assertEqual(TestSubClass.sub_foo, 'stuff')
        self.assertEqual(TestSubClass.sub_bar, None)
        self.assertEqual(TestSubClass.static_foobar('stuff'), 'substuff')

        inst = TestSubSubClass('stuff')
        self.assertEqual(inst.subsub_foo, 'stuff')
        self.assertEqual(inst.subsub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'subsubstuff')
        self.assertEqual(TestSubSubClass.subsub_foo, 'stuff')
        self.assertEqual(TestSubSubClass.subsub_bar, None)
        self.assertEqual(TestSubSubClass.static_foobar('stuff'), 'subsubstuff')

        self.assertEqual(history, [])

    def test_weave_class_slots(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.Proceed(*args)
            yield aspectlib.Return('bar')

        inst = SlotsTestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(SlotsTestClass.class_foo, 'stuff')
        self.assertEqual(SlotsTestClass.class_bar, None)
        self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'stuff')

        inst = SlotsTestClass()
        with aspectlib.weave(SlotsTestClass, aspect):
            inst = SlotsTestClass('stuff')
            self.assertEqual(inst.foo, 'stuff')
            self.assertEqual(inst.bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(SlotsTestClass.class_foo, 'stuff')
            self.assertEqual(SlotsTestClass.class_bar, ':)')
            self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (SlotsTestClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

            inst = SlotsTestSubClass('stuff')
            self.assertEqual(inst.sub_foo, 'stuff')
            self.assertEqual(inst.sub_bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(SlotsTestSubClass.class_sub_foo, 'stuff')
            self.assertEqual(SlotsTestSubClass.class_sub_bar, ':)')
            self.assertEqual(SlotsTestSubClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (SlotsTestSubClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

            inst = SlotsTestSubSubClass('stuff')
            self.assertEqual(inst.subsub_foo, 'stuff')
            self.assertEqual(inst.subsub_bar, ':)')
            self.assertEqual(inst.inst, 'bar')
            self.assertEqual(inst.klass, 'bar')
            self.assertEqual(inst.static, 'bar')
            self.assertEqual(SlotsTestSubSubClass.class_subsub_foo, 'stuff')
            self.assertEqual(SlotsTestSubSubClass.class_subsub_bar, ':)')
            self.assertEqual(SlotsTestSubSubClass.static_foobar('stuff'), 'bar')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (SlotsTestSubSubClass, 'stuff'),
                ('stuff',),
                ('stuff',),
            ])
            del history[:]

        inst = SlotsTestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(SlotsTestClass.class_foo, 'stuff')
        self.assertEqual(SlotsTestClass.class_bar, None)
        self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'stuff')

        inst = SlotsTestSubClass('stuff')
        self.assertEqual(inst.sub_foo, 'stuff')
        self.assertEqual(inst.sub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'substuff')
        self.assertEqual(SlotsTestSubClass.class_sub_foo, 'stuff')
        self.assertEqual(SlotsTestSubClass.class_sub_bar, None)
        self.assertEqual(SlotsTestSubClass.static_foobar('stuff'), 'substuff')

        inst = SlotsTestSubSubClass('stuff')
        self.assertEqual(inst.subsub_foo, 'stuff')
        self.assertEqual(inst.subsub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'subsubstuff')
        self.assertEqual(SlotsTestSubSubClass.class_subsub_foo, 'stuff')
        self.assertEqual(SlotsTestSubSubClass.class_subsub_bar, None)
        self.assertEqual(SlotsTestSubSubClass.static_foobar('stuff'), 'subsubstuff')

        self.assertEqual(history, [])


    def test_weave_class_on_init(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.Proceed(*args)
            yield aspectlib.Return('bar')

        inst = SlotsTestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(SlotsTestClass.class_foo, 'stuff')
        self.assertEqual(SlotsTestClass.class_bar, None)
        self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'stuff')

        inst = SlotsTestClass()
        with aspectlib.weave(SlotsTestClass, aspect, on_init=True):

            inst = SlotsTestClass('stuff')
            self.assertEqual(inst.foo, 'stuff')
            self.assertEqual(inst.bar, None)
            self.assertEqual(inst.inst, None)
            self.assertEqual(inst.foobar('bluff'), 'bar')
            self.assertEqual(inst.foo, 'bluff')
            self.assertEqual(inst.bar, ':)')
            self.assertEqual(inst.class_foobar('bluff'), 'bar')
            self.assertEqual(SlotsTestClass.class_foo, 'bluff')
            self.assertEqual(SlotsTestClass.class_bar, ':)')
            self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'bar')

            inst = SlotsTestSubClass('stuff')
            self.assertEqual(inst.sub_foo, 'stuff')
            self.assertEqual(inst.sub_bar, None)
            self.assertEqual(inst.inst, None)
            self.assertEqual(inst.foobar('bluff'), 'bar')
            self.assertEqual(inst.sub_foo, 'bluff')
            self.assertEqual(inst.sub_bar, ':)')
            self.assertEqual(inst.class_foobar('bluff'), 'bar')
            self.assertEqual(SlotsTestSubClass.class_sub_foo, 'bluff')
            self.assertEqual(SlotsTestSubClass.class_sub_bar, ':)')
            self.assertEqual(SlotsTestSubClass.static_foobar('stuff'), 'bar')

            inst = SlotsTestSubSubClass('stuff')
            self.assertEqual(inst.subsub_foo, 'stuff')
            self.assertEqual(inst.subsub_bar, None)
            self.assertEqual(inst.inst, None)
            self.assertEqual(inst.foobar('bluff'), 'bar')
            self.assertEqual(inst.subsub_foo, 'bluff')
            self.assertEqual(inst.subsub_bar, ':)')
            self.assertEqual(inst.class_foobar('bluff'), 'bar')
            self.assertEqual(SlotsTestSubSubClass.class_subsub_foo, 'bluff')
            self.assertEqual(SlotsTestSubSubClass.class_subsub_bar, ':)')
            self.assertEqual(SlotsTestSubSubClass.static_foobar('stuff'), 'bar')

        del history[:]

        inst = SlotsTestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(SlotsTestClass.class_foo, 'stuff')
        self.assertEqual(SlotsTestClass.class_bar, None)
        self.assertEqual(SlotsTestClass.static_foobar('stuff'), 'stuff')

        inst = SlotsTestSubClass('stuff')
        self.assertEqual(inst.sub_foo, 'stuff')
        self.assertEqual(inst.sub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'substuff')
        self.assertEqual(SlotsTestSubClass.class_sub_foo, 'stuff')
        self.assertEqual(SlotsTestSubClass.class_sub_bar, None)
        self.assertEqual(SlotsTestSubClass.static_foobar('stuff'), 'substuff')

        inst = SlotsTestSubSubClass('stuff')
        self.assertEqual(inst.subsub_foo, 'stuff')
        self.assertEqual(inst.subsub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'subsubstuff')
        self.assertEqual(SlotsTestSubSubClass.class_subsub_foo, 'stuff')
        self.assertEqual(SlotsTestSubSubClass.class_subsub_bar, None)
        self.assertEqual(SlotsTestSubSubClass.static_foobar('stuff'), 'subsubstuff')

        self.assertEqual(history, [])

    def test_weave_class_old_style(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.Proceed(*args)
            yield aspectlib.Return('bar')

        inst = LegacyTestClass()

        with aspectlib.weave(LegacyTestClass, aspect, skip_subclasses=True):
            with aspectlib.weave(LegacyTestSubClass, aspect, skip_subclasses=True):
                with aspectlib.weave(LegacyTestSubSubClass, aspect, skip_subclasses=True):
                    inst = LegacyTestClass('stuff')
                    self.assertEqual(inst.foo, 'stuff')
                    self.assertEqual(inst.bar, ':)')
                    self.assertEqual(inst.inst, 'bar')
                    self.assertEqual(inst.klass, 'bar')
                    self.assertEqual(inst.static, 'bar')
                    self.assertEqual(LegacyTestClass.foo, 'stuff')
                    self.assertEqual(LegacyTestClass.bar, ':)')
                    self.assertEqual(LegacyTestClass.static_foobar('stuff'), 'bar')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestClass, 'stuff'),
                        ('stuff',),
                        ('stuff',),
                    ])
                    del history[:]

                    inst = LegacyTestSubClass('stuff')
                    self.assertEqual(inst.sub_foo, 'stuff')
                    self.assertEqual(inst.sub_bar, ':)')
                    self.assertEqual(inst.inst, 'bar')
                    self.assertEqual(inst.klass, 'bar')
                    self.assertEqual(inst.static, 'bar')
                    self.assertEqual(LegacyTestSubClass.sub_foo, 'stuff')
                    self.assertEqual(LegacyTestSubClass.sub_bar, ':)')
                    self.assertEqual(LegacyTestSubClass.static_foobar('stuff'), 'bar')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestSubClass, 'stuff'),
                        ('stuff',),
                        ('stuff',),
                    ])
                    del history[:]

                    inst = LegacyTestSubSubClass('stuff')
                    self.assertEqual(inst.subsub_foo, 'stuff')
                    self.assertEqual(inst.subsub_bar, ':)')
                    self.assertEqual(inst.inst, 'bar')
                    self.assertEqual(inst.klass, 'bar')
                    self.assertEqual(inst.static, 'bar')
                    self.assertEqual(LegacyTestSubSubClass.subsub_foo, 'stuff')
                    self.assertEqual(LegacyTestSubSubClass.subsub_bar, ':)')
                    self.assertEqual(LegacyTestSubSubClass.static_foobar('stuff'), 'bar')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestSubSubClass, 'stuff'),
                        ('stuff',),
                        ('stuff',),
                    ])
                    del history[:]

        inst = LegacyTestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')
        self.assertEqual(inst.bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'stuff')
        self.assertEqual(LegacyTestClass.foo, 'stuff')
        self.assertEqual(LegacyTestClass.bar, None)
        self.assertEqual(LegacyTestClass.static_foobar('stuff'), 'stuff')

        inst = LegacyTestSubClass('stuff')
        self.assertEqual(inst.sub_foo, 'stuff')
        self.assertEqual(inst.sub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'substuff')
        self.assertEqual(LegacyTestSubClass.sub_foo, 'stuff')
        self.assertEqual(LegacyTestSubClass.sub_bar, None)
        self.assertEqual(LegacyTestSubClass.static_foobar('stuff'), 'substuff')

        inst = LegacyTestSubSubClass('stuff')
        self.assertEqual(inst.subsub_foo, 'stuff')
        self.assertEqual(inst.subsub_bar, None)
        self.assertEqual(inst.inst, None)
        self.assertEqual(inst.klass, None)
        self.assertEqual(inst.static, 'subsubstuff')
        self.assertEqual(LegacyTestSubSubClass.subsub_foo, 'stuff')
        self.assertEqual(LegacyTestSubSubClass.subsub_bar, None)
        self.assertEqual(LegacyTestSubSubClass.static_foobar('stuff'), 'subsubstuff')

        self.assertEqual(history, [])

    def test_weave_class_all_magic(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            yield aspectlib.Proceed

        inst = TestClass()

        with aspectlib.weave(TestClass, aspect, skip_magic_methods=False):
            inst = TestClass('stuff')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (inst, 'stuff'),
                (TestClass, 'stuff'),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubClass('stuff')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (inst, 'stuff'),
                (TestSubClass, 'stuff'),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubSubClass('stuff')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (inst, 'stuff'),
                (TestSubSubClass, 'stuff'),
                ('stuff',),
            ])
            del history[:]

        inst = TestClass('stuff')
        inst = TestSubClass('stuff')
        inst = TestSubSubClass('stuff')

        self.assertEqual(history, [])

    def test_weave_class_old_style_all_magic(self):
        history = []

        @aspectlib.Aspect
        def aspect(*args):
            history.append(args)
            yield aspectlib.Proceed

        inst = LegacyTestClass()

        with aspectlib.weave(LegacyTestClass, aspect, skip_subclasses=True):
            with aspectlib.weave(LegacyTestSubClass, aspect, skip_subclasses=True):
                with aspectlib.weave(LegacyTestSubSubClass, aspect, skip_subclasses=True):
                    inst = LegacyTestClass('stuff')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestClass, 'stuff'),
                        ('stuff',),
                    ])
                    del history[:]

                    inst = LegacyTestSubClass('stuff')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestSubClass, 'stuff'),
                        ('stuff',),
                    ])
                    del history[:]

                    inst = LegacyTestSubSubClass('stuff')
                    self.assertEqual(history, [
                        (inst, 'stuff'),
                        (LegacyTestSubSubClass, 'stuff'),
                        ('stuff',),
                    ])
                    del history[:]

        inst = LegacyTestClass('stuff')
        inst = LegacyTestSubClass('stuff')
        inst = LegacyTestSubSubClass('stuff')

        self.assertEqual(history, [])

    def test_just_proceed(self):
        @aspectlib.Aspect
        def aspect():
            yield aspectlib.Proceed

        @aspect
        def func():
            return 'stuff'

        self.assertEqual(func(), 'stuff')

    def test_just_proceed_with_error(self):
        @aspectlib.Aspect
        def aspect():
            yield aspectlib.Proceed

        @aspect
        def func():
            1/0

        self.assertRaises(ZeroDivisionError, func)

    def test_weave_unknown(self):
        @aspectlib.Aspect
        def aspect():
            yield aspectlib.Proceed

        self.assertRaises(RuntimeError, aspectlib.weave, 1, aspect)

    def test_weave_subclass(self, Bub=Sub):
        with aspectlib.weave(Sub, mock(returns='foobar'), on_init=True):
            self.assertEqual(Sub().meth(), 'foobar')
            self.assertEqual(Bub().meth(), 'base')
        self.assertEqual(Sub().meth(), 'base')
        self.assertTrue(Bub is Sub)

    def test_weave_subclass_meth_manual(self):
        with aspectlib.weave(Sub, mock(returns='foobar'), on_init=True, only_methods=['meth']):
            self.assertEqual(Sub().meth(), 'foobar')

        self.assertEqual(Sub().meth(), 'base')

    def test_weave_subclass_meth_auto(self):
        with aspectlib.weave(Sub.meth, mock(returns='foobar'), on_init=True):
            self.assertEqual(Sub().meth(), 'foobar')

        self.assertEqual(Sub().meth(), 'base')

    def test_weave_multiple(self):
        with aspectlib.weave((module_func, module_func2), mock(returns='foobar')):
            self.assertEqual(module_func(), 'foobar')
            self.assertEqual(module_func2(), 'foobar')

        self.assertEqual(module_func(), None)
        self.assertEqual(module_func2(), None)


def module_func():
    pass


def module_func2():
    pass


class TestClass(object):
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


class TestSubClass(TestClass):
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


class TestSubSubClass(TestSubClass):
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


if __name__ == '__main__':
    unittest.main()
