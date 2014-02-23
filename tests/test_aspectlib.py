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
        def aspect(self, foo):
            self.foo = 'bar'
            yield aspectlib.return_

        with aspectlib.weave(TestClass.foobar, aspect):
            inst = TestClass('stuff')
            self.assertEqual(inst.foo, 'bar')

        inst = TestClass('stuff')
        self.assertEqual(inst.foo, 'stuff')

    def test_weave_instance_meth(self):
        @aspectlib.aspect
        def aspect(self, foo):
            self.foo = 'bar'
            yield aspectlib.return_

        inst = TestClass()

        with aspectlib.weave(inst.foobar, aspect):
            inst.__init__('stuff')
            self.assertEqual(inst.foo, 'bar')

        inst.__init__('stuff')
        self.assertEqual(inst.foo, 'stuff')


def module_func():
    pass


class TestClass(object):
    def __init__(self, foo=None):
        self.foobar(foo)

    def foobar(self, foo):
        self.foo = foo

class TestSubClass(TestClass):
    def foobar(self, foo):
        self.boo = foo

if __name__ == '__main__':
    unittest.main()
