try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from datetime import timedelta

import asyncio
from tornado import gen
from tornado import ioloop

from aspectlib import debug


def test_decorate_asyncio_coroutine():
    buf = StringIO()

    @asyncio.coroutine
    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    def coro():
        yield from asyncio.sleep(0.01)
        return "result"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(coro())
    output = buf.getvalue()
    assert 'coro => %r' % 'result' in output


def test_decorate_tornado_coroutine():
    buf = StringIO()

    @gen.coroutine
    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    def coro():
        yield gen.Task(loop.add_timeout, timedelta(microseconds=10))
        return "result"

    loop = ioloop.IOLoop.current()
    loop.run_sync(coro)
    output = buf.getvalue()
    assert 'coro => %r' % 'result' in output
