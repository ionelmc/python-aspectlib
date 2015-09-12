# encoding: utf8
from __future__ import print_function

import pytest

import aspectlib


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
        return a
        yield

    gen = func(0)
    result = pytest.raises(StopIteration, gen.__next__ if hasattr(gen, '__next__') else gen.next)
    assert result.value.args == (0,)
