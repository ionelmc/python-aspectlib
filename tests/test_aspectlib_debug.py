from __future__ import print_function

import logging

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

LOG_TEST_SIMPLE = '''^some_meth\(1, 2, 3, a=4\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_simple.*
some_meth => \.\.\.\.\.\.\.\.\.\t
\x0b\x0c\r\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\. !"#\$%&\'\(\)\*\+,-\./0123456789:;<=>\?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\[\\\]\^_`abcdefghijklmnopqrstuvwxyz\{\|\}~\.+
$'''


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
        with aspectlib.weave(some_meth, aspectlib.debug.log(print_to=buf, module=False, stacktrace=2)):
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

        @aspectlib.debug.log
        def foo():
            pass
        foo()
        self.assertRegexpMatches(buf.getvalue(), 'foo\(\) +<<<.*\nfoo => None\n')

    def test_attributes(self):
        buf = StringIO()
        with aspectlib.weave(MyStuff, aspectlib.debug.log(
            print_to=buf,
            stacktrace=2,
            module=False,
            attributes=('foo', 'bar()')
        ), skip_methods=('bar',)):
            MyStuff('bar').stuff()
        print(buf.getvalue())
        self.assertRegexpMatches(buf.getvalue(), "^\{MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{MyStuff foo='bar' bar='foo'\}.stuff => bar\n$")
        MyStuff('bar').stuff()
        self.assertRegexpMatches(buf.getvalue(), "^\{MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{MyStuff foo='bar' bar='foo'\}.stuff => bar\n$")

