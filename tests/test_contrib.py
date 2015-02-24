from logging import getLogger

import pytest

from aspectlib import contrib
from aspectlib.contrib import retry
from aspectlib.test import LogCapture


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


def test_with_class():
    logger = getLogger(__name__)

    class Connection(object):
        count = 0

        @retry
        def __init__(self, address):
            self.address = address
            self.__connect()

        def __connect(self, *_, **__):
            self.count += 1
            if self.count % 3:
                raise OSError("Failed")
            else:
                logger.info("connected!")

        @retry(cleanup=__connect)
        def action(self, arg1, arg2):
            self.count += 1
            if self.count % 3 == 0:
                raise OSError("Failed")
            else:
                logger.info("action!")

        def __repr__(self):
            return "Connection@%s" % self.count

    with LogCapture([logger, contrib.logger]) as logcap:
        try:
            conn = Connection("to-something")
            for i in range(5):
                conn.action(i, i)
        finally:
            for i in logcap.messages:
                print(i)
    assert logcap.messages == [
        ('ERROR', "__init__((Connection@1, 'to-something'), {}) raised exception Failed. 5 retries left. Sleeping 0 secs."),
        ('ERROR', "__init__((Connection@2, 'to-something'), {}) raised exception Failed. 4 retries left. Sleeping 0 secs."),
        ('INFO', 'connected!'),
        ('INFO', 'action!'),
        ('INFO', 'action!'),
        ('ERROR', 'action((Connection@6, 2, 2), {}) raised exception Failed. 5 retries left. Sleeping 0 secs.'),
        ('ERROR', 'action((Connection@7, 2, 2), {}) raised exception Failed. 4 retries left. Sleeping 0 secs.'),
        ('ERROR', 'action((Connection@8, 2, 2), {}) raised exception Failed. 3 retries left. Sleeping 0 secs.'),
        ('INFO', 'connected!'),
        ('INFO', 'action!'),
        ('INFO', 'action!'),
        ('ERROR', 'action((Connection@12, 4, 4), {}) raised exception Failed. 5 retries left. Sleeping 0 secs.'),
        ('ERROR', 'action((Connection@13, 4, 4), {}) raised exception Failed. 4 retries left. Sleeping 0 secs.'),
        ('ERROR', 'action((Connection@14, 4, 4), {}) raised exception Failed. 3 retries left. Sleeping 0 secs.'),
        ('INFO', 'connected!'),
        ('INFO', 'action!'),
    ]
