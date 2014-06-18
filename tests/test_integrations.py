from __future__ import print_function

import os
import re
import socket
import warnings

import pytest
from process_tests import dump_on_error
from process_tests import wait_for_strings

import aspectlib
from aspectlib.test import mock
from aspectlib.test import record
from aspectlib.utils import PYPY

try:
    import thread
except ImportError:
    import _thread as thread

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

LOG_TEST_SOCKET = r"""^\{_?socket(object)?\}.connect\(\('127.0.0.1', 1\)\) +<<< .*tests[\/]test_integrations.py:\d+:test_socket.*
\{_?socket(object)?\}.connect \~ raised .*(ConnectionRefusedError|error)\((10061|111), .*refused.*\)"""


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
    with aspectlib.weave(target, aspectlib.debug.log(
        print_to=buf,
        stacktrace=4,
        module=False
    ), lazy=True):
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
    with aspectlib.weave(
        socket.socket,
        aspectlib.debug.log(print_to=buf, stacktrace=False),
        lazy=True,
        methods=aspectlib.ALL_METHODS
    ):
        s = socket.socket()

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
            ['socket._fileobject' if aspectlib.PY2 else 'socket.SocketIO'] +
            (['socket.socket', 'socket._realsocket'] if aspectlib.PY2 else ['socket.socket']),
            aspectlib.debug.log(print_to=buf, stacktrace=False),
            lazy=True,
            methods=aspectlib.ALL_METHODS,
        ):
            s = socket.socket()
            s.settimeout(1)
            s.connect(p.getsockname())
            if aspectlib.PY3:
                fh = s.makefile('rwb', buffering=0)
            else:
                fh = s.makefile(bufsize=0)
            fh.write(b"STUFF\n")
            fh.readline()

        with dump_on_error(buf.getvalue):
            wait_for_strings(
                buf.getvalue, 0,
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
            if aspectlib.PY3:
                f = c.makefile('rw', buffering=1)
            else:
                f = c.makefile(bufsize=1)
            while f.readline():
                f.write('-\n')
        finally:
            os._exit(0)


def test_weave_os_module():
    calls = []

    with aspectlib.weave('os', record(calls=calls, extended=True), methods="getenv|walk"):
        os.getenv('BUBU', 'bubu')
        os.walk('.')

    assert calls == [
        (None, 'os.getenv', ('BUBU', 'bubu'), {}),
        (None, 'os.walk', ('.',), {})
    ]
