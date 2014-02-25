from __future__ import print_function

import unittest

import aspectlib


class AOPTestCase(unittest.TestCase):

    def test_aspect_bad(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            return "crap"

        @aspect.decorate
        def func():
            pass

        self.assertRaises(RuntimeError, func)

    def test_aspect_return(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            yield aspectlib.return_

        @aspect.decorate
        def func():
            return 'stuff'

        self.assertEqual(func(), None)

    def test_aspect_return_value(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            yield aspectlib.return_('stuff')

        @aspect.decorate
        def func():
            pass

        self.assertEqual(func(), 'stuff')

    def test_aspect_raise(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            try:
                yield aspectlib.proceed
            except ZeroDivisionError:
                pass
            else:
                raise AssertionError("didn't raise")

            yield aspectlib.return_('stuff')

        @aspect.decorate
        def func():
            1/0

        self.assertEqual(func(), 'stuff')

    def test_aspect_raise_from_aspect(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            1/0

        @aspect.decorate
        def func():
            pass

        self.assertRaises(ZeroDivisionError, func)

    def test_aspect_return_but_call(self):
        calls = []

        @aspectlib.aspect
        def aspect(arg):
            assert 'first' == (yield aspectlib.proceed)
            assert 'second' == (yield aspectlib.proceed('second'))
            yield aspectlib.return_('stuff')

        @aspect.decorate
        def func(arg):
            calls.append(arg)
            return arg

        self.assertEqual(func('first'), 'stuff')
        self.assertEqual(calls, ['first', 'second'])

    def test_weave_func(self):
        @aspectlib.aspect
        def aspect(*args, **kwargs):
            yield aspectlib.return_('stuff')

        with aspectlib.weave(module_func, aspect):
            self.assertEqual(module_func(), 'stuff')

        self.assertEqual(module_func(), None)

    def test_weave_class_meth(self):
        @aspectlib.aspect
        def aspect(self, *_):
            self.foo = 'bar'
            yield aspectlib.return_

        with aspectlib.weave(TestClass.foobar, aspect):
            inst = TestClass('stuff')
            self.assertEqual(inst.foo, 'bar')
            inst.foobar()

        inst = TestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')

    def test_weave_instance_meth(self):
        @aspectlib.aspect
        def aspect(self):
            self.foo = 'bar'
            yield aspectlib.return_

        inst = TestClass()
        with aspectlib.weave(inst.foobar, aspect):
            inst.foobar()
            self.assertEqual(inst.foo, 'bar')

        inst.foobar('stuff')
        self.assertEqual(inst.foo, 'stuff')

    def test_weave_class(self):
        history = []

        @aspectlib.aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.proceed(*args)
            yield aspectlib.return_('bar')

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

    def test_weave_class_old_style(self):
        history = []

        @aspectlib.aspect
        def aspect(*args):
            history.append(args)
            args += ':)',
            yield aspectlib.proceed(*args)
            yield aspectlib.return_('bar')

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

        @aspectlib.aspect
        def aspect(*args):
            history.append(args)
            yield aspectlib.proceed

        inst = TestClass()

        with aspectlib.weave(TestClass, aspect, skip_magic_methods=False):
            inst = TestClass('stuff')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (TestClass, 'stuff'),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubClass('stuff')
            self.assertEqual(history, [
                (inst, 'stuff'),
                (TestSubClass, 'stuff'),
                ('stuff',),
            ])
            del history[:]

            inst = TestSubSubClass('stuff')
            self.assertEqual(history, [
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

        @aspectlib.aspect
        def aspect(*args):
            history.append(args)
            yield aspectlib.proceed

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
        @aspectlib.aspect
        def aspect():
            yield aspectlib.proceed

        @aspect.decorate
        def func():
            return 'stuff'

        self.assertEqual(func(), 'stuff')

    def test_just_proceed_with_error(self):
        @aspectlib.aspect
        def aspect():
            yield aspectlib.proceed

        @aspect.decorate
        def func():
            1/0

        self.assertRaises(ZeroDivisionError, func)

    def test_weave_unknown(self):
        @aspectlib.aspect
        def aspect():
            yield aspectlib.proceed

        self.assertRaises(RuntimeError, aspectlib.weave, 1, aspect)


def module_func():
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


if __name__ == '__main__':
    unittest.main()
