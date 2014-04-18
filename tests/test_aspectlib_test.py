from __future__ import print_function

from pytest import raises

from aspectlib import PY2
from aspectlib.test import format_calls
from aspectlib.test import mock
from aspectlib.test import record
from aspectlib.test import Story
from aspectlib.test import StoryResultWrapper
from aspectlib.test import Unexpected

from test_pkg1.test_pkg2 import test_mod


def module_fun(a, b=2):
    pass


def module_fun2(a, b=2):
    pass


exc = RuntimeError()


def rfun():
    raise exc


def nfun(a, b=2):
    return a, b


def test_record():
    fun = record(nfun)

    assert fun(2, 3) == (2, 3)
    assert fun(3, b=4) == (3, 4)
    assert fun.calls == [
        (None, (2, 3), {}),
        (None, (3, ), {'b': 4}),
    ]


def test_record_result():
    fun = record(results=True)(nfun)

    assert fun(2, 3) == (2, 3)
    assert fun(3, b=4) == (3, 4)
    assert fun.calls == [
        (None, (2, 3), {}, (2, 3), None),
        (None, (3, ), {'b': 4}, (3, 4), None),
    ]


def test_record_exception():
    fun = record(results=True)(rfun)

    raises(RuntimeError, fun)
    assert fun.calls == [
        (None, (), {}, None, exc),
    ]


def test_record_result_callback():
    calls = []

    fun = record(results=True, callback=lambda *args: calls.append(args))(nfun)

    assert fun(2, 3) == (2, 3)
    assert fun(3, b=4) == (3, 4)
    assert calls == [
        (None, 'test_aspectlib_test.nfun', (2, 3), {}, (2, 3), None),
        (None, 'test_aspectlib_test.nfun', (3, ), {'b': 4}, (3, 4), None),
    ]


def test_record_exception_callback():
    calls = []

    fun = record(results=True, callback=lambda *args: calls.append(args))(rfun)

    raises(RuntimeError, fun)
    assert calls == [
        (None, 'test_aspectlib_test.rfun', (), {}, None, exc),
    ]


def test_record_callback():
    calls = []

    fun = record(callback=lambda *args: calls.append(args))(nfun)

    assert fun(2, 3) == (2, 3)
    assert fun(3, b=4) == (3, 4)
    assert calls == [
        (None, 'test_aspectlib_test.nfun', (2, 3), {}),
        (None, 'test_aspectlib_test.nfun', (3, ), {'b': 4}),
    ]


def test_record_with_no_call():
    called = []

    @record(iscalled=False)
    def fun():
        called.append(True)

    assert fun() is None
    assert fun.calls == [
        (None, (), {}),
    ]
    assert called == []


def test_record_with_call():
    called = []

    @record
    def fun():
        called.append(True)

    fun()
    assert fun.calls == [
        (None, (), {}),
    ]
    assert called == [True]


def test_record_as_context():
    with record(module_fun) as history:
        module_fun(2, 3)
        module_fun(3, b=4)

    assert history.calls == [
        (None, (2, 3), {}),
        (None, (3, ), {'b': 4}),
    ]
    del history.calls[:]

    module_fun(2, 3)
    module_fun(3, b=4)
    assert history.calls == []


def test_bad_mock():
    raises(TypeError, mock)
    raises(TypeError, mock, call=False)


def test_simple_mock():
    assert "foobar" == mock("foobar")(module_fun)(1)


def test_mock_no_calls():
    with record(module_fun) as history:
        assert "foobar" == mock("foobar")(module_fun)(2)
    assert history.calls == []


def test_mock_with_calls():
    with record(module_fun) as history:
        assert "foobar" == mock("foobar", call=True)(module_fun)(3)
    assert history.calls == [(None, (3,), {})]


def test_double_recording():
    with record(module_fun) as history:
        with record(module_fun2) as history2:
            module_fun(2, 3)
            module_fun2(2, 3)

    assert history.calls == [
        (None, (2, 3), {}),
    ]
    del history.calls[:]
    assert history2.calls == [
        (None, (2, 3), {}),
    ]
    del history2.calls[:]

    module_fun(2, 3)
    assert history.calls == []
    assert history2.calls == []


def test_record_not_iscalled_and_results():
    raises(AssertionError, record, module_fun, iscalled=False, results=True)
    record(module_fun, iscalled=False, results=False)
    record(module_fun, iscalled=True, results=True)
    record(module_fun, iscalled=True, results=False)


def test_story_empty_play_noproxy():
    with Story(test_mod).replay(recurse_lock=True, proxy=False, strict=False) as replay:
        raises(AssertionError, test_mod.target)

    assert replay._calls.actual == {}


def test_story_empty_play_proxy():
    assert test_mod.target() is None
    raises(TypeError, test_mod.target, 123)

    with Story(test_mod).replay(recurse_lock=True, proxy=True, strict=False) as replay:
        assert test_mod.target() is None
        raises(TypeError, test_mod.target, 123)

    assert format_calls(replay._calls.actual) == format_calls({
        ('test_pkg1.test_pkg2.test_mod.target', (), frozenset([])): (
            None, None
        ),
        ('test_pkg1.test_pkg2.test_mod.target', (123,), frozenset([])): (
            None, TypeError('target() takes no arguments (1 given)'
                            if PY2
                            else 'target() takes 0 positional arguments but 1 was given',)
        )
    })


def test_story_empty_play_noproxy_class():
    with Story(test_mod).replay(recurse_lock=True, proxy=False, strict=False) as replay:
        raises(AssertionError, test_mod.Stuff, 1, 2)

    assert replay._calls.actual == {}


def test_story_half_play_noproxy_class():
    with Story(test_mod) as story:
        obj = test_mod.Stuff(1, 2)

    with story.replay(recurse_lock=True, proxy=False, strict=False):
        obj = test_mod.Stuff(1, 2)
        raises(AssertionError, obj.mix, 3, 4)


def test_story_text_helpers():
    with Story(test_mod) as story:
        obj = test_mod.Stuff(1, 2)
        test_mod.target(1) == 2
        test_mod.target(2) == 3
        obj.meth('a') == 'x'
        obj.meth('b') == 'x'
        obj = test_mod.Stuff(2, 3)
        obj.meth('c') == 'x'

    with story.replay(recurse_lock=True, strict=False) as replay:
        obj = test_mod.Stuff(1, 2)
        obj.meth('a')
        test_mod.target(1)
        obj.meth()
        test_mod.func(5)

        obj = test_mod.Stuff(4, 4)
        obj.meth()

    print (replay.missing())
    assert replay.missing() == """stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)
stuff_1.meth('b') == 'x'  # returns
stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(2, 3)  # was never called !
stuff_2.meth('c') == 'x'  # returns
test_pkg1.test_pkg2.test_mod.target(2) == 3  # returns
"""
    print (replay.unexpected())
    assert replay.unexpected() == """stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)
stuff_1.meth() == None  # returns
stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(4, 4)  # was never called !
stuff_2.meth() == None  # returns
test_pkg1.test_pkg2.test_mod.func(5) == None  # returns
"""
    print (replay.diff())
    assert replay.diff() == """--- expected
+++ actual
@@ -1,7 +1,7 @@
 stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)
 stuff_1.meth('a') == 'x'  # returns
-stuff_1.meth('b') == 'x'  # returns
-stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(2, 3)
-stuff_2.meth('c') == 'x'  # returns
+stuff_1.meth() == None  # returns
+stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(4, 4)  # was never called !
+stuff_2.meth() == None  # returns
+test_pkg1.test_pkg2.test_mod.func(5) == None  # returns
 test_pkg1.test_pkg2.test_mod.target(1) == 2  # returns
-test_pkg1.test_pkg2.test_mod.target(2) == 3  # returns
""" or replay.diff() == """--- expected """ """
+++ actual """ """
@@ -1,7 +1,7 @@
 stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)
 stuff_1.meth('a') == 'x'  # returns
-stuff_1.meth('b') == 'x'  # returns
-stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(2, 3)
-stuff_2.meth('c') == 'x'  # returns
+stuff_1.meth() == None  # returns
+stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(4, 4)  # was never called !
+stuff_2.meth() == None  # returns
+test_pkg1.test_pkg2.test_mod.func(5) == None  # returns
 test_pkg1.test_pkg2.test_mod.target(1) == 2  # returns
-test_pkg1.test_pkg2.test_mod.target(2) == 3  # returns
"""


def test_story_empty_play_proxy_class_missing_report():
    with Story(test_mod).replay(recurse_lock=True, proxy=True, strict=False) as replay:
        obj = test_mod.Stuff(1, 2)
        obj.mix(3, 4)
        obj.mix('a', 'b')
        raises(ValueError, obj.raises, 123)
        obj = test_mod.Stuff(0, 1)
        obj.mix('a', 'b')
        obj.mix(3, 4)
        test_mod.target()
        raises(ValueError, test_mod.raises, 'badarg')
        raises(ValueError, obj.raises, 123)
        test_mod.ThatLONGStuf(1).mix(2)
        test_mod.ThatLONGStuf(3).mix(4)
        obj = test_mod.ThatLONGStuf(1)
        obj.mix()
        obj.meth()
        obj.mix(10)

    print(repr(replay.diff()))

    assert replay.diff() == """--- expected
+++ actual
@@ -0,0 +1,17 @@
+stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(0, 1)  # was never called !
+stuff_1.mix('a', 'b') == (0, 1, 'a', 'b')  # returns
+stuff_1.mix(3, 4) == (0, 1, 3, 4)  # returns
+stuff_1.raises(123) ** ValueError((123,))  # raises
+stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)  # was never called !
+stuff_2.mix('a', 'b') == (1, 2, 'a', 'b')  # returns
+stuff_2.mix(3, 4) == (1, 2, 3, 4)  # returns
+stuff_2.raises(123) ** ValueError((123,))  # raises
+that_long_stuf_1 = test_pkg1.test_pkg2.test_mod.ThatLONGStuf(1)  # was never called !
+that_long_stuf_1.meth() == None  # returns
+that_long_stuf_1.mix() == (1,)  # returns
+that_long_stuf_1.mix(10) == (1, 10)  # returns
+that_long_stuf_1.mix(2) == (1, 2)  # returns
+that_long_stuf_2 = test_pkg1.test_pkg2.test_mod.ThatLONGStuf(3)  # was never called !
+that_long_stuf_2.mix(4) == (3, 4)  # returns
+test_pkg1.test_pkg2.test_mod.raises('badarg') ** ValueError(('badarg',))  # raises
+test_pkg1.test_pkg2.test_mod.target() == None  # returns
""" or replay.diff() == """--- expected """ """
+++ actual """ """
@@ -1,0 +1,17 @@
+stuff_1 = test_pkg1.test_pkg2.test_mod.Stuff(0, 1)  # was never called !
+stuff_1.mix('a', 'b') == (0, 1, 'a', 'b')  # returns
+stuff_1.mix(3, 4) == (0, 1, 3, 4)  # returns
+stuff_1.raises(123) ** ValueError((123,))  # raises
+stuff_2 = test_pkg1.test_pkg2.test_mod.Stuff(1, 2)  # was never called !
+stuff_2.mix('a', 'b') == (1, 2, 'a', 'b')  # returns
+stuff_2.mix(3, 4) == (1, 2, 3, 4)  # returns
+stuff_2.raises(123) ** ValueError((123,))  # raises
+that_long_stuf_1 = test_pkg1.test_pkg2.test_mod.ThatLONGStuf(1)  # was never called !
+that_long_stuf_1.meth() == None  # returns
+that_long_stuf_1.mix() == (1,)  # returns
+that_long_stuf_1.mix(10) == (1, 10)  # returns
+that_long_stuf_1.mix(2) == (1, 2)  # returns
+that_long_stuf_2 = test_pkg1.test_pkg2.test_mod.ThatLONGStuf(3)  # was never called !
+that_long_stuf_2.mix(4) == (3, 4)  # returns
+test_pkg1.test_pkg2.test_mod.raises('badarg') ** ValueError(('badarg',))  # raises
+test_pkg1.test_pkg2.test_mod.target() == None  # returns
"""


def test_story_empty_play_proxy_class():
    assert test_mod.Stuff(1, 2).mix(3, 4) == (1, 2, 3, 4)

    with Story(test_mod).replay(recurse_lock=True, proxy=True, strict=False) as replay:
        obj = test_mod.Stuff(1, 2)
        assert obj.mix(3, 4) == (1, 2, 3, 4)
        assert obj.mix('a', 'b') == (1, 2, 'a', 'b')

        raises(TypeError, obj.meth, 123)

        obj = test_mod.Stuff(0, 1)
        assert obj.mix('a', 'b') == (0, 1, 'a', 'b')
        assert obj.mix(3, 4) == (0, 1, 3, 4)

        raises(TypeError, obj.meth, 123)

    assert format_calls(replay._calls.actual) == format_calls({
        ('test_pkg1.test_pkg2.test_mod.Stuff', (1, 2), frozenset([])): Unexpected({
            ('mix', ('a', 'b'), frozenset([])): ((1, 2, 'a', 'b'), None),
            ('mix', (3, 4), frozenset([])): ((1, 2, 3, 4), None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        }),
        ('test_pkg1.test_pkg2.test_mod.Stuff', (0, 1), frozenset([])): Unexpected({
            ('mix', ('a', 'b'), frozenset([])): ((0, 1, 'a', 'b'), None),
            ('mix', (3, 4), frozenset([])): ((0, 1, 3, 4), None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        })
    })


def test_story_half_play_proxy_class():
    assert test_mod.Stuff(1, 2).mix(3, 4) == (1, 2, 3, 4)

    with Story(test_mod) as story:
        obj = test_mod.Stuff(1, 2)
        obj.mix(3, 4) == (1, 2, 3, 4)

    with story.replay(recurse_lock=True, proxy=True, strict=False) as replay:
        obj = test_mod.Stuff(1, 2)
        assert obj.mix(3, 4) == (1, 2, 3, 4)
        assert obj.meth() is None

        raises(TypeError, obj.meth, 123)

        obj = test_mod.Stuff(0, 1)
        assert obj.mix('a', 'b') == (0, 1, 'a', 'b')
        assert obj.mix(3, 4) == (0, 1, 3, 4)

        raises(TypeError, obj.meth, 123)
    assert replay.unexpected() == format_calls({
        ('test_pkg1.test_pkg2.test_mod.Stuff', (1, 2), frozenset([])): {
            ('meth', (), frozenset([])): (None, None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        },
        ('test_pkg1.test_pkg2.test_mod.Stuff', (0, 1), frozenset([])): Unexpected({
            ('mix', ('a', 'b'), frozenset([])): ((0, 1, 'a', 'b'), None),
            ('mix', (3, 4), frozenset([])): ((0, 1, 3, 4), None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        })
    })


def test_story_full_play_noproxy():
    with Story(test_mod) as story:
        test_mod.target(123) == 'foobar'
        test_mod.target(1234) ** ValueError

    with story.replay(recurse_lock=True, proxy=False, strict=False, dump=False) as replay:
        raises(AssertionError, test_mod.target)
        assert test_mod.target(123) == 'foobar'
        raises(ValueError, test_mod.target, 1234)

    assert replay.unexpected() == ""


def test_story_full_play_noproxy_dump():
    with Story(test_mod) as story:
        test_mod.target(123) == 'foobar'
        test_mod.target(1234) ** ValueError

    with story.replay(recurse_lock=True, proxy=False, strict=False, dump=True) as replay:
        raises(AssertionError, test_mod.target)
        assert test_mod.target(123) == 'foobar'
        raises(ValueError, test_mod.target, 1234)

    assert replay.unexpected() == ""


def test_story_full_play_proxy():
    with Story(test_mod) as story:
        test_mod.target(123) == 'foobar'
        test_mod.target(1234) ** ValueError

    with story.replay(recurse_lock=True, proxy=True, strict=False) as replay:
        assert test_mod.target() is None
        assert test_mod.target(123) == 'foobar'
        raises(ValueError, test_mod.target, 1234)
        raises(TypeError, test_mod.target, 'asdf')

    assert replay.unexpected() == format_calls({
        ('test_pkg1.test_pkg2.test_mod.target', (), frozenset([])): (
            None, None
        ),
        ('test_pkg1.test_pkg2.test_mod.target', ('asdf',), frozenset([])): (
            None, TypeError('target() takes no arguments (1 given)'
                            if PY2
                            else 'target() takes 0 positional arguments but 1 was given',)
        )
    })


def test_story_result_wrapper():
    x = StoryResultWrapper(lambda *a: None)
    raises(AttributeError, setattr, x, 'stuff', 1)
    raises(AttributeError, getattr, x, 'stuff')
    raises(TypeError, lambda: x >> 2)
    raises(TypeError, lambda: x << 1)
    raises(TypeError, lambda: x > 1)
    x == 1
    x ** Exception()


def test_story_result_wrapper_bad_exception():
    x = StoryResultWrapper(lambda *a: None)
    raises(RuntimeError, lambda: x ** 1)
    x ** Exception
    x ** Exception('boom!')


def test_story_create():
    with Story(test_mod) as story:
        test_mod.target('a', 'b', 'c') == 'abc'
        test_mod.target() ** Exception
        test_mod.target(1, 2, 3) == 'foobar'
        obj = test_mod.Stuff('stuff')
        assert isinstance(obj, test_mod.Stuff)
        obj.meth('other', 1, 2) == 123
        obj.mix('other') == 'mixymix'

    assert story._calls == {
        ('test_pkg1.test_pkg2.test_mod.Stuff', ('stuff',), frozenset()): {
            ('meth', ('other', 1, 2), frozenset()): (123, None),
            ('mix', ('other',), frozenset()): ('mixymix', None)
        },
        ('test_pkg1.test_pkg2.test_mod.target', (), frozenset()): (None, Exception),
        ('test_pkg1.test_pkg2.test_mod.target', (1, 2, 3), frozenset()): ('foobar', None),
        ('test_pkg1.test_pkg2.test_mod.target', ('a', 'b', 'c'), frozenset()): ('abc', None)
    }

def xtest_story_empty_play_proxy_class_dependencies():
    with Story(test_mod).replay(recurse_lock=True, proxy=True, strict=False) as replay:
        obj = test_mod.Stuff(1, 2)
        other = obj.other('x')
        raises(ValueError, other.raises, 'badarg')
        other.mix(3, 4)
        obj = test_mod.Stuff(0, 1)
        obj.mix(3, 4)
        other = obj.other(2)
        other.mix(3, 4)

    print(repr(replay.diff()))

    assert replay.diff() == ""
