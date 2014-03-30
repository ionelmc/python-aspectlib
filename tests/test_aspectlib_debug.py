from __future__ import print_function

import logging
import re

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
some_meth => \.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\. !"#\$%&\'\(\)\*\+,-\./0123456789:;<=>\?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\[\\\]\^_`abcdefghijklmnopqrstuvwxyz\{\|\}~\.+
$'''


class MyStuff(object):
    def __init__(self, foo):
        self.foo = foo

    def bar(self):
        return 'foo'

    def stuff(self):
        return self.foo

class OldStuff:
    def __init__(self, foo):
        self.foo = foo

    def bar(self):
        return 'foo'

    def stuff(self):
        return self.foo


def test_simple():
    buf = StringIO()
    with aspectlib.weave(some_meth, aspectlib.debug.log(print_to=buf, module=False, stacktrace=10)):
        some_meth(1, 2, 3, a=4)

    assert re.match(LOG_TEST_SIMPLE, buf.getvalue())
    some_meth(1, 2, 3, a=4)
    assert re.match(LOG_TEST_SIMPLE, buf.getvalue())


def test_fail_to_log():
    @aspectlib.debug.log(print_to="crap")
    def foo():
        pass
    foo()


def test_logging_works():
    buf = StringIO()
    ch = logging.StreamHandler(buf)
    ch.setLevel(logging.DEBUG)
    aspectlib.debug.logger.addHandler(ch)

    @aspectlib.debug.log
    def foo():
        pass
    foo()
    assert re.match('foo\(\) +<<<.*\nfoo => None\n', buf.getvalue())


def test_attributes():
    buf = StringIO()
    with aspectlib.weave(MyStuff, aspectlib.debug.log(
        print_to=buf,
        stacktrace=10,
        attributes=('foo', 'bar()')
    ), methods='(?!bar)(?!__.*__$)'):
        MyStuff('bar').stuff()
    print(buf.getvalue())
    assert re.match("^\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())
    MyStuff('bar').stuff()
    assert re.match("^\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())


def test_no_stack():
    buf = StringIO()
    with aspectlib.weave(MyStuff, aspectlib.debug.log(
        print_to=buf,
        stacktrace=None,
        attributes=('foo', 'bar()')
    ), methods='(?!bar)(?!__.*__$)'):
        MyStuff('bar').stuff()
    print(buf.getvalue())
    assert "{test_aspectlib_debug.MyStuff foo='bar' bar='foo'}.stuff()\n{test_aspectlib_debug.MyStuff foo='bar' bar='foo'}.stuff => bar\n" == buf.getvalue()


def test_attributes_old_style():
    buf = StringIO()
    with aspectlib.weave(OldStuff, aspectlib.debug.log(
        print_to=buf,
        stacktrace=10,
        attributes=('foo', 'bar()')
    ), methods='(?!bar)(?!__.*__$)'):
        OldStuff('bar').stuff()
    print(repr(buf.getvalue()))
    assert re.match("^\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())
    MyStuff('bar').stuff()
    assert re.match("^\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())


def test_no_stack_old_style():
    buf = StringIO()
    with aspectlib.weave(OldStuff, aspectlib.debug.log(
        print_to=buf,
        stacktrace=None,
        attributes=('foo', 'bar()')
    ), methods='(?!bar)(?!__.*__$)'):
        OldStuff('bar').stuff()
    print(buf.getvalue())
    assert "{test_aspectlib_debug.OldStuff foo='bar' bar='foo'}.stuff()\n{test_aspectlib_debug.OldStuff foo='bar' bar='foo'}.stuff => bar\n" == buf.getvalue()

#test log with old-style class
