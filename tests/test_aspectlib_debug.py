from __future__ import print_function

import logging
import re
import sys
import weakref
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pytest

import aspectlib
import aspectlib.debug


LOG_TEST_SIMPLE = r'''^some_meth\(1, 2, 3, a=4\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_simple.*
some_meth => \.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\. !"#\$%&\'\(\)\*\+,-\./0123456789:;<=>\?@ABCDEFGHIJKLMNOPQRSTUVWXYZ\[\\\]\^_`abcdefghijklmnopqrstuvwxyz\{\|\}~\.+
$'''


def some_meth(*_args, **_kwargs):
    return ''.join(chr(i) for i in range(255))


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
    assert re.match(r'foo\(\) +<<<.*\nfoo => None\n', buf.getvalue())


def test_attributes():
    buf = StringIO()
    with aspectlib.weave(MyStuff, aspectlib.debug.log(
        print_to=buf,
        stacktrace=10,
        attributes=('foo', 'bar()')
    ), methods='(?!bar)(?!__.*__$)'):
        MyStuff('bar').stuff()
    print(buf.getvalue())
    assert re.match(r"^\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())
    MyStuff('bar').stuff()
    assert re.match(r"^\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.MyStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())


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
    assert re.match(r"^\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())
    MyStuff('bar').stuff()
    assert re.match(r"^\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff\(\) +<<< .*tests/test_aspectlib_debug.py:\d+:test_attributes.*\n\{test_aspectlib_debug.OldStuff foo='bar' bar='foo'\}.stuff => bar\n$", buf.getvalue())


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


@pytest.mark.skipif(sys.version_info < (2, 7), reason="No weakref.WeakSet on Python<=2.6")
def test_weakref():
    with aspectlib.weave(MyStuff, aspectlib.debug.log):
        s = weakref.WeakSet()
        s.add(MyStuff.stuff)
        print(list(s))
    print(list(s))


@pytest.mark.skipif(sys.version_info < (2, 7), reason="No weakref.WeakSet on Python<=2.6")
def test_weakref_oldstyle():
    with aspectlib.weave(OldStuff, aspectlib.debug.log):
        s = weakref.WeakSet()
        s.add(MyStuff.stuff)
        print(list(s))
    print(list(s))
