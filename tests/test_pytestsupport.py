from aspectlib import test


class Foo(object):
    def bar(self):
        return 1


def test_fixture_1(weave):
    weave(Foo.bar, test.mock(2))
    assert Foo().bar() == 2


def test_fixture_2(weave):
    assert Foo().bar() == 1

    with weave(Foo.bar, test.mock(2)):
        assert Foo().bar() == 2

    assert Foo().bar() == 1
