import asyncio
import os
import re
import socket
import warnings
from datetime import timedelta

import pytest
from process_tests import dump_on_error
from process_tests import wait_for_strings
from tornado import gen
from tornado import ioloop

import aspectlib
from aspectlib import debug
from aspectlib.test import mock
from aspectlib.test import record
from aspectlib.utils import PYPY

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

LOG_TEST_SOCKET = r"""^\{_?socket(object)?\}.connect\(\('127.0.0.1', 1\)\) +<<< .*tests[\/]test_integrations.py:\d+:test_socket.*
\{_?socket(object)?\}.connect \~ raised .*(ConnectionRefusedError|error)\((10061|111|61), .*refused.*\)"""


def test_mock_builtin():
    with aspectlib.weave(open, mock('foobar')):
        assert open('???') == 'foobar'

    assert open(__file__) != 'foobar'


def test_mock_builtin_os():
    print(os.open.__name__)
    with aspectlib.weave('os.open', mock('foobar')):
        assert os.open('???') == 'foobar'

    assert os.open(__file__, 0) != 'foobar'


def test_record_warning():
    with aspectlib.weave('warnings.warn', record):
        warnings.warn('crap')
        assert warnings.warn.calls == [(None, ('crap',), {})]


@pytest.mark.skipif(not hasattr(os, 'fork'), reason="os.fork not available")
def test_fork():
    with aspectlib.weave('os.fork', mock('foobar')):
        pid = os.fork()
        if not pid:
            os._exit(0)
        assert pid == 'foobar'

    pid = os.fork()
    if not pid:
        os._exit(0)
    assert pid != 'foobar'


def test_socket(target=socket.socket):
    buf = StringIO()
    with aspectlib.weave(target, aspectlib.debug.log(print_to=buf, stacktrace=4, module=False), lazy=True):
        s = socket.socket()
        try:
            s.connect(('127.0.0.1', 1))
        except Exception:
            pass

    print(buf.getvalue())
    assert re.match(LOG_TEST_SOCKET, buf.getvalue())

    s = socket.socket()
    try:
        s.connect(('127.0.0.1', 1))
    except Exception:
        pass

    assert re.match(LOG_TEST_SOCKET, buf.getvalue())


def test_socket_as_string_target():
    test_socket(target='socket.socket')


def test_socket_meth(meth=socket.socket.close):
    calls = []
    with aspectlib.weave(meth, record(calls=calls)):
        s = socket.socket()
        assert s.close() is None
    assert calls == [(s, (), {})]
    del calls[:]

    s = socket.socket()
    assert s.close() is None
    assert calls == []


def test_socket_meth_as_string_target():
    test_socket_meth('socket.socket.close')


def test_socket_all_methods():
    buf = StringIO()
    with aspectlib.weave(socket.socket, aspectlib.debug.log(print_to=buf, stacktrace=False), lazy=True, methods=aspectlib.ALL_METHODS):
        socket.socket()

    assert "}.__init__ => None" in buf.getvalue()


@pytest.mark.skipif(not hasattr(os, 'fork') or PYPY, reason="os.fork not available or PYPY")
def test_realsocket_makefile():
    buf = StringIO()
    p = socket.socket()
    p.bind(('127.0.0.1', 0))
    p.listen(1)
    p.settimeout(1)
    pid = os.fork()

    if pid:
        with aspectlib.weave(
            ['socket.SocketIO', 'socket.socket'],
            aspectlib.debug.log(print_to=buf, stacktrace=False),
            lazy=True,
            methods=aspectlib.ALL_METHODS,
        ):
            s = socket.socket()
            s.settimeout(1)
            s.connect(p.getsockname())
            fh = s.makefile('rwb', buffering=0)
            fh.write(b"STUFF\n")
            fh.readline()

        with dump_on_error(buf.getvalue):
            wait_for_strings(
                buf.getvalue,
                0,
                "}.connect",
                "}.makefile",
                "}.write(",
                "}.send",
                "}.write =>",
                "}.readline()",
                "}.recv",
                "}.readline => ",
            )
    else:
        try:
            c, _ = p.accept()
            c.settimeout(1)
            f = c.makefile('rw', buffering=1)
            while f.readline():
                f.write('-\n')
        finally:
            os._exit(0)


def test_weave_os_module():
    calls = []

    with aspectlib.weave('os', record(calls=calls, extended=True), methods="getenv|walk"):
        os.getenv('BUBU', 'bubu')
        os.walk('.')

    assert calls == [(None, 'os.getenv', ('BUBU', 'bubu'), {}), (None, 'os.walk', ('.',), {})]


def test_decorate_asyncio_coroutine():
    buf = StringIO()

    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    async def coro():
        await asyncio.sleep(0.01)
        return "result"

    loop = asyncio.new_event_loop()
    loop.run_until_complete(coro())
    output = buf.getvalue()
    print(output)
    assert 'coro => %r' % 'result' in output


def test_decorate_tornado_coroutine():
    buf = StringIO()

    @gen.coroutine
    @debug.log(print_to=buf, module=False, stacktrace=2, result_repr=repr)
    def coro():
        if hasattr(gen, 'Task'):
            yield gen.Task(loop.add_timeout, timedelta(microseconds=10))
        else:
            yield gen.sleep(0.01)
        return "result"

    asyncio_loop = asyncio.new_event_loop()
    try:
        get_event_loop = asyncio.get_event_loop
        asyncio.get_event_loop = lambda: asyncio_loop
        loop = ioloop.IOLoop.current()
        loop.run_sync(coro)
    finally:
        asyncio.get_event_loop = get_event_loop
    output = buf.getvalue()
    assert 'coro => %r' % 'result' in output
