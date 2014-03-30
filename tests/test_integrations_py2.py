try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import asyncio

from aspectlib import debug

def test_decorate_coroutine():
    buf = StringIO()

    @asyncio.coroutine
    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    def coro():
        yield asyncio.From(asyncio.sleep(0.01))
        raise StopIteration("result")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(coro())
    output = buf.getvalue()
    assert 'coro => %r' % 'result'
