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

    result = consume(func(0))
    assert result is None


def consume(gen):
    ret = []

    def it():
        ret.append((yield from gen))

    list(it())
    return ret[0]


def test_aspect_chain_on_generator_yield_from():
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
    assert consume(gen) == 0


def test_aspect_chain_on_generator_no_return_yield_from():
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
    assert consume(gen) is None
