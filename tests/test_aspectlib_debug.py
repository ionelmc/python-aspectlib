from __future__ import print_function

import re
import logging
import socket

import aspectlib
import aspectlib.debug

try:
    import unittest2 as unittest
except ImportError:
    import unittest
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def some_meth(*args, **kwargs):
    return ''.join(chr(i) for i in range(255))

LOG_TEST_SIMPLE = '''^some_meth\(1, 2, 3, a=4\) +<<< aspectlib/debug\.py:\d+:logged
some_meth => \.\.\.\.\.\.\.\.\.\t
\x0b\x0c\r\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\. !"#\$%&\'\(\)\*\+,-\./0123456789:;<=>\?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\[\\\]\^_`abcdefghijklmnopqrstuvwxyz\{\|\}~\.+
$'''
LOG_TEST_SOCKET = """^<_?socket(object)?>.connect\(\('127.0.0.1', 1\)\) +<<< aspectlib/debug.py:\d+:logged
<_?socket(object)?>.connect\(\('127.0.0.1', 1\)\) +<<< aspectlib/debug.py:\d+:logged ~ raised \[Errno 111\] Connection refused\n$"""

class MyStuff(object):
    def __init__(self, foo):
        self.foo = foo

    def bar(self):
        return 'foo'

    def stuff(self):
        return self.foo

class LoggerTestCase(unittest.TestCase):
    maxDiff = None

    def test_simple(self):
        buf = StringIO()
        with aspectlib.weave(some_meth, aspectlib.debug.log(print_to=buf, stacktrace=1)):
            some_meth(1, 2, 3, a=4)

        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SIMPLE)
        some_meth(1, 2, 3, a=4)
        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SIMPLE)

    def test_fail_to_log(self):
        @aspectlib.debug.log(print_to="crap")
        def foo():
            pass
        foo()

    def test_logging_works(self):
        buf = StringIO()
        ch = logging.StreamHandler(buf)
        ch.setLevel(logging.DEBUG)
        aspectlib.debug.logger.addHandler(ch)

        @aspectlib.debug.log(use_logging=True)
        def foo():
            pass
        foo()
        self.assertRegexpMatches(buf.getvalue(), 'foo\(\) +<<<.*\nfoo => None\n')

    def test_attributes(self):
        buf = StringIO()
        with aspectlib.weave(MyStuff, aspectlib.debug.log(print_to=buf, stacktrace=1, instance_attributes=('foo', 'bar()')), skip_methods=('bar',)):
            MyStuff('bar').stuff()
        print(buf.getvalue())
        self.assertRegexpMatches(buf.getvalue(), "^<MyStuff foo='bar' bar='foo'>.stuff\(\) +<<< aspectlib/debug.py:\d+:logged\n<MyStuff foo='bar' bar='foo'>.stuff => bar\n$")
        MyStuff('bar').stuff()
        self.assertRegexpMatches(buf.getvalue(), "^<MyStuff foo='bar' bar='foo'>.stuff\(\) +<<< aspectlib/debug.py:\d+:logged\n<MyStuff foo='bar' bar='foo'>.stuff => bar\n$")

                                                  #"<MyStuff foo='bar'>.bar() +<<< aspectlib/debug.py:67:logged\n<MyStuff foo='bar'>.bar => foo\n<MyStuff foo='bar' bar='foo'>.stuff()                         <<< aspectlib/debug.py:67:logged\n<MyStuff foo='bar' bar='foo'>.stuff => bar\n"

    def test_socket(self):
        buf = StringIO()
        with aspectlib.weave(socket.socket, aspectlib.debug.log(print_to=buf, stacktrace=1), patch_on_init=True):
            s = socket.socket()
            try:
                s.connect(('127.0.0.1', 1))
            except Exception:
                pass

        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SOCKET)

        s = socket.socket()
        try:
            s.connect(('127.0.0.1', 1))
        except Exception:
            pass

        self.assertRegexpMatches(buf.getvalue(), LOG_TEST_SOCKET)
