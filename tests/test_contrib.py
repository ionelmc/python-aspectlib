import time

import pytest

from aspectlib.test import Story, record, mock
from aspectlib.contrib import retry
from aspectlib import weave

def flaky_func(arg):
    if arg:
        arg.pop()
        raise OSError('Tough luck!')


def test_done_suceess():
    calls = []
    @retry
    def ok_func():
        calls.append(1)

    ok_func()
    assert calls == [1]

def test_defaults():
    calls = []
    retry(sleep=calls.append)(flaky_func)([None] * 5)
    assert calls == [0, 0, 0, 0, 0]


def test_raises():
    calls = []
    pytest.raises(OSError, retry(sleep=calls.append)(flaky_func), [None] * 6)
    assert calls == [0, 0, 0, 0, 0]

    calls = []
    pytest.raises(OSError, retry(sleep=calls.append, retries=1)(flaky_func), [None, None])
    assert calls == [0]


def test_backoff():
    calls = []
    retry(sleep=calls.append, backoff=1.5)(flaky_func)([None] * 5)
    assert calls == [1.5, 1.5, 1.5, 1.5, 1.5]


def test_backoff_exponential():
    calls = []
    retry(sleep=calls.append, retries=10, backoff=retry.exponential_backoff)(flaky_func)([None] * 10)
    print(calls)
    assert calls == [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]


def test_backoff_straight():
    calls = []
    retry(sleep=calls.append, retries=10, backoff=retry.straight_backoff)(flaky_func)([None] * 10)
    print(calls)
    assert calls == [1, 2, 5, 10, 15, 20, 25, 30, 35, 40]


def test_backoff_flat():
    calls = []
    retry(sleep=calls.append, retries=10, backoff=retry.flat_backoff)(flaky_func)([None] * 10)
    print(calls)
    assert calls == [1, 2, 5, 10, 15, 30, 60, 60, 60, 60]
