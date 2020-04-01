# encoding: utf8
from __future__ import print_function

import pytest

import aspectlib
from aspectlib.utils import PY37plus

pytestmark = pytest.mark.skipif(PY37plus, reason="Tests are incompatible with PEP-479")


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
