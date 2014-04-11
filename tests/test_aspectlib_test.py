from __future__ import print_function

from pytest import raises

from aspectlib.test import record, mock


def module_fun(a, b=2):
    pass


def module_fun2(a, b=2):
    pass


def test_record():
    @record
    def fun(a, b=2):
        pass

    fun(2, 3)
    fun(3, b=4)
    assert fun.calls == [
        (None, (2, 3), {}),
        (None, (3, ), {'b': 4}),
    ]


def test_record_result():
    @record(results=True)
    def fun(a, b=2):
        return a, b

    fun(2, 3)
    fun(3, b=4)
    assert fun.calls == [
        (None, (2, 3), {}, (2, 3), None),
        (None, (3, ), {'b': 4}, (3, 4), None),
    ]


def test_record_exception():
    exc = RuntimeError()

    @record(results=True)
    def fun():
        raise exc

    raises(RuntimeError, fun)
    assert fun.calls == [
        (None, (), {}, None, exc),
    ]


def test_record_result_callback():
    calls = []

    @record(results=True, callback=lambda *args: calls.append(args))
    def fun(a, b=2):
        return a, b

    fun(2, 3)
    fun(3, b=4)
    assert calls == [
        (None, 'fun', (2, 3), {}, (2, 3), None),
        (None, 'fun', (3, ), {'b': 4}, (3, 4), None),
    ]


def test_record_exception_callback():
    exc = RuntimeError()
    calls = []

    @record(results=True, callback=lambda *args: calls.append(args))
    def fun():
        raise exc

    raises(RuntimeError, fun)
    assert calls == [
        (None, 'fun', (), {}, None, exc),
    ]


def test_record_callback():
    calls = []

    @record(callback=lambda *args: calls.append(args))
    def fun(a, b=2):
        pass

    fun(2, 3)
    fun(3, b=4)
    assert calls == [
        (None, 'fun', (2, 3), {}),
        (None, 'fun', (3, ), {'b': 4}),
    ]


def test_record_with_no_call():
    called = []
    @record(iscalled=False)
    def fun():
        called.append(True)

    fun()
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
