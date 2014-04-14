from __future__ import print_function

import os

from pytest import raises

from aspectlib.test import record, mock, Story, StoryResultWrapper, unexpected
from aspectlib import PY2

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
    with Story(test_mod).replay() as replay:
        raises(AssertionError, test_mod.target)

    assert replay.calls.unexpected == {}

def test_story_empty_play_proxy():
    assert test_mod.target() is None
    raises(TypeError, test_mod.target, 123)

    with Story(test_mod).replay(proxy=True) as replay:
        assert test_mod.target() is None
        raises(TypeError, test_mod.target, 123)

    assert repr(replay.calls.unexpected) == repr({
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
    with Story(test_mod).replay() as replay:
        raises(AssertionError, test_mod.Stuff, 1, 2)

    assert replay.calls.unexpected == {}


def test_story_half_play_noproxy_class():
    with Story(test_mod) as story:
        obj = test_mod.Stuff(1, 2)

    with story.replay():
        obj = test_mod.Stuff(1, 2)
        raises(AssertionError, obj.mix, 3, 4)


def test_story_empty_play_proxy_class():
    assert test_mod.Stuff(1, 2).mix(3, 4) == (1, 2, 3, 4)

    with Story(test_mod).replay(proxy=True) as replay:
        obj = test_mod.Stuff(1, 2)
        assert obj.mix(3, 4) == (1, 2, 3, 4)
        assert obj.mix('a', 'b') == (1, 2, 'a', 'b')

        raises(TypeError, obj.meth, 123)

        obj = test_mod.Stuff(0, 1)
        assert obj.mix('a', 'b') == (0, 1, 'a', 'b')
        assert obj.mix(3, 4) == (0, 1, 3, 4)

        raises(TypeError, obj.meth, 123)
    from pprint import pprint as print

    print(replay.calls.unexpected)
    assert repr(replay.calls.unexpected) == repr({
        ('test_pkg1.test_pkg2.test_mod.Stuff', (1, 2), frozenset([])): unexpected({
            ('mix', ('a', 'b'), frozenset([])): ((1, 2, 'a', 'b'), None),
            ('mix', (3, 4), frozenset([])): ((1, 2, 3, 4), None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        }),
        ('test_pkg1.test_pkg2.test_mod.Stuff', (0, 1), frozenset([])): unexpected({
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

    with story.replay(proxy=True) as replay:
        obj = test_mod.Stuff(1, 2)
        assert obj.mix(3, 4) == (1, 2, 3, 4)
        assert obj.meth() is None

        raises(TypeError, obj.meth, 123)

        obj = test_mod.Stuff(0, 1)
        assert obj.mix('a', 'b') == (0, 1, 'a', 'b')
        assert obj.mix(3, 4) == (0, 1, 3, 4)

        raises(TypeError, obj.meth, 123)
    from pprint import pprint as print

    print(replay.calls.unexpected)
    assert repr(replay.calls.unexpected) == repr({
        ('test_pkg1.test_pkg2.test_mod.Stuff', (1, 2), frozenset([])): {
            ('meth', (), frozenset([])): (None, None),
            ('meth', (123,), frozenset([])): (None, TypeError('meth() takes exactly 1 argument (2 given)'
                                                              if PY2
                                                              else 'meth() takes 1 positional argument but 2 were given',))
        },
        ('test_pkg1.test_pkg2.test_mod.Stuff', (0, 1), frozenset([])): unexpected({
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

    with story.replay() as replay:
        raises(AssertionError, test_mod.target)
        assert test_mod.target(123) == 'foobar'
        raises(ValueError, test_mod.target, 1234)

    assert replay.calls.unexpected == {}


def test_story_full_play_proxy():
    with Story(test_mod) as story:
        test_mod.target(123) == 'foobar'
        test_mod.target(1234) ** ValueError

    with story.replay(proxy=True) as replay:
        assert test_mod.target() is None
        assert test_mod.target(123) == 'foobar'
        raises(ValueError, test_mod.target, 1234)
        raises(TypeError, test_mod.target, 'asdf')

    assert repr(replay.calls.unexpected) == repr({
        ('test_pkg1.test_pkg2.test_mod.target', (), frozenset([])): (
            None, None
        ),
        ('test_pkg1.test_pkg2.test_mod.target', ('asdf',), frozenset([])): (
            None, TypeError('target() takes no arguments (1 given)'
                            if PY2
                            else 'target() takes 0 positional arguments but 1 was given',)
        )
    })


#def test_story_play_proxy():
#    with Story('os') as story:
#        os.listdir() == 'mocked'
#        os.listdir(None) ** ValueError
#        os.listdir(123) ** ValueError('bad value')
#
#    with story.proxy():
#        os.listdir('.')
#        assert os.listdir() == 'mocked'
#        raises(ValueError, os.listdir, None)
#        raises(ValueError, os.listdir, 123)
#
#def test_story_play_noproxy():
#    with Story('os').play():
#        raises(RuntimeError, os.listdir, '.')
#        raises(RuntimeError, os.listdir)

#def test_story_check_proxy
#def xtest_story():
#    with Story('os') as story:
#        os.listdir('.') == ['stuff']
#        os.listdir(None) ** RuntimeError
#
#    with story(proxy=True):
#        assert os.listdir('.') == ['stuff']
#        raises(RuntimeError, os.listdir(None))
#        os.listdir('/')  # this isn't in the story but works
#
#    with story(proxy=False):  # run the story completely isolated - aka a "stub", see
#        # http://martinfowler.com/articles/mocksArentStubs.html#TheDifferenceBetweenMocksAndStubs
#        assert os.listdir('.') == ['stuff']
#        raises(RuntimeError, os.listdir, None)
#        raises(AssertionError, os.listdir, '/')  # unknown arg '/'
#
#    with story(proxy=False, checked=True):  # run the story as a "mock" (see MF)
#        assert os.listdir('.') == ['stuff']
#        raises(AssertionError, os.listdir, '/')  # unknown arg '/'
#    # will raise AssertionError as os.listdir(None) was specified in the Story by not actually called
#
#    with story(proxy=True, checked=True):  # aka
#        assert os.listdir('.') == ['stuff']
#        raises(AssertionError, os.listdir, '/')  # unknown arg '/'
#        # will raise AssertionError as os.listdir(None) was specified in the Story by not actually called


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

    assert story.calls == {
        ('test_pkg1.test_pkg2.test_mod.Stuff', ('stuff',), frozenset()): {
            ('meth', ('other', 1, 2), frozenset()): (123, None),
            ('mix', ('other',), frozenset()): ('mixymix', None)
        },
        ('test_pkg1.test_pkg2.test_mod.target', (), frozenset()): (None, Exception),
        ('test_pkg1.test_pkg2.test_mod.target', (1, 2, 3), frozenset()): ('foobar', None),
        ('test_pkg1.test_pkg2.test_mod.target', ('a', 'b', 'c'), frozenset()): ('abc', None)
    }
