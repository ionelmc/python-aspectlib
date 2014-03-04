from collections import namedtuple
from contextlib import contextmanager
from functools import wraps

from wrapt.decorators import FunctionWrapper

import aspectlib

_Call = namedtuple('Call', ('self', 'args', 'kwargs'))
_DEFAULT = object()
_DEFAULT_FALSE = object()


def mock(returns=_DEFAULT, call=_DEFAULT_FALSE):
    assert call and call is not _DEFAULT_FALSE or returns is not _DEFAULT, "`call` must be True if `returns` is DEFAULT !"

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if call and call is not _DEFAULT_FALSE:
                value = func(*args, **kwargs)
            if returns is not _DEFAULT:
                return returns
            else:
                return value
        return wrapper
    return decorator


class _RecordWrapper(FunctionWrapper):
    def __enter__(self):
        self.entanglement = aspectlib.weave(self.__wrapped__, lambda _: self)
        return self.__wrapped__

    def __exit__(self, *args):
        self.entanglement.rollback()


def record(wrapped):
    def record_wrapper(wrapped, instance, args, kwargs):
        calls.append(_Call(instance, args, kwargs))
        return wrapped(*args, **kwargs)
    recorded = _RecordWrapper(wrapped, record_wrapper)
    calls = recorded.calls = []
    return recorded
