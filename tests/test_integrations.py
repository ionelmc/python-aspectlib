from __future__ import print_function

import os
import socket
import warnings

import aspectlib
from aspectlib.test import mock
from aspectlib.test import record

try:
    import unittest2 as unittest
    from unittest2.case import skipIf
except ImportError:
    import unittest
    from unittest.case import skipIf

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

LOG_TEST_SOCKET = r"""^\{_?socket(object)?\}.connect\(\('127.0.0.1', 1\)\) +<<< .*tests/test_integrations.py:\d+:test_socket.*
\{_?socket(object)?\}.connect \~ raised .*(ConnectionRefusedError|error)\((10061|111), '.*refused.*'\)\n$"""


class AOPTestCase(unittest.TestCase):
    def test_mock_builtin(self):
        with aspectlib.weave(open, mock('foobar')):
            self.assertEqual(open('???'), 'foobar')

        self.assertNotEqual(open(__file__), 'foobar')

    def test_record_warning(self):
        with aspectlib.weave('warnings.warn', record):
            warnings.warn('crap')
            self.assertEqual(warnings.warn.calls, [(None, ('crap',), {})])

    @skipIf(not hasattr(os, 'fork'), "os.fork not available")
    def test_fork(self):
        with aspectlib.weave('os.fork', mock('foobar')):
            pid = os.fork()
            if not pid:
                os._exit(0)
            self.assertEqual(pid, 'foobar')

        pid = os.fork()
        if not pid:
            os._exit(0)
        self.assertNotEqual(pid, 'foobar')

    def test_socket(self, target=socket.socket):
        buf = StringIO()
        with aspectlib.weave(target, aspectlib.debug.log(
            print_to=buf,
            stacktrace=2,
            module=False
        ), on_init=True):
            s = socket.socket()
            try:
                s.connect(('127.0.0.1', 1))
            except Exception:
                pass

        print(buf.getvalue())
        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SOCKET)

        s = socket.socket()
        try:
            s.connect(('127.0.0.1', 1))
        except Exception:
            pass

        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SOCKET)

    def test_socket_as_string_target(self):
        self.test_socket(target='socket.socket')

