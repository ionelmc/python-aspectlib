try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from datetime import timedelta
import pytest
import sys
import trollius as asyncio
from tornado import gen
from tornado import ioloop
try:
    import MySQLdb
except ImportError:
    MySQLdb = None

from aspectlib import debug, weave, ALL_METHODS
from aspectlib.test import Story


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

@pytest.mark.skipif(not MySQLdb, reason="No MySQLdb installed")
def test_mysql():
    with Story(['MySQLdb.cursors.BaseCursor', 'MySQLdb.connections.Connection']) as story:
        pass
    rows = []
    with story.replay(strict=False) as replay:
        import MySQLdb
        con = MySQLdb.connect('localhost', 'root', '')
        con.select_db('mysql')
        cursor = con.cursor()
        cursor.execute('show tables')
        rows.extend(cursor.fetchall())
    assert '== (%s)' % ', '.join(repr(row) for row in rows) in replay.unexpected
