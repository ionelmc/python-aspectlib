try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from datetime import timedelta

import asyncio
from tornado import gen
from tornado import ioloop

from aspectlib import debug, weave, ALL_METHODS


def test_decorate_asyncio_coroutine():
    buf = StringIO()

    @asyncio.coroutine
    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    def coro():
        yield asyncio.From(asyncio.sleep(0.01))
        raise StopIteration("result")

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
        raise StopIteration("result")

    loop = ioloop.IOLoop.current()
    loop.run_sync(coro)
    output = buf.getvalue()
    assert 'coro => %r' % 'result' in output

#def test_mysql():
#    buf = StringIO()
#
#    with weave(
#        ['MySQLdb.connections.Connection', 'MySQLdb.cursors.BaseCursor'],
#        debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr),
#        methods=ALL_METHODS
#    ):
#        con = MySQLdb.connections.Connection('localhost', 'root', '')
#        con.select_db('mysql')
#        cursor = con.cursor()
#        cursor.execute('show tables')
#        print(cursor.fetchall())
