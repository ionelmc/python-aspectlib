import asyncio

from aspectlib import debug

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def test_decorate_asyncio_coroutine():
    buf = StringIO()

    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    async def coro():
        await asyncio.sleep(0.01)
        return "result"

    loop = asyncio.get_event_loop()
    loop.run_until_complete(coro())
    output = buf.getvalue()
    print(output)
    assert 'coro => %r' % 'result' in output
