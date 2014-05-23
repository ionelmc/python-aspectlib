===============================
Testing with ``aspectlib.test``
===============================

Spy & mock toolkit: ``record``/``mock`` decorators
==================================================

.. highlights::

    Lightweight spies and mock responses


Example usage, suppose you want to test this class:

    >>> class ProductionClass(object):
    ...     def method(self):
    ...         return 'stuff'
    >>> real = ProductionClass()

With :obj:`aspectlib.test.mock` and :obj:`aspectlib.test.record`::

    >>> from aspectlib import weave, test
    >>> patch = weave(real.method, [test.mock(3), test.record])
    >>> real.method(3, 4, 5, key='value')
    3
    >>> assert real.method.calls == [(real, (3, 4, 5), {'key': 'value'})]

As a bonus, you have an easy way to rollback all the mess::

    >>> patch.rollback()
    >>> real.method()
    'stuff'

With ``mock``::

    >>> from mock import Mock
    >>> real = ProductionClass()
    >>> real.method = Mock(return_value=3)
    >>> real.method(3, 4, 5, key='value')
    3
    >>> real.method.assert_called_with(3, 4, 5, key='value')

Capture-replay toolkit: ``Story`` and ``Replay``
================================================

.. highlights::

    Elaborate tools for testing difficult code

Writing tests using the :obj:`Story <aspectlib.test.Story>` is viable when neither `integration tests
<http://en.wikipedia.org/wiki/Integration_testing>`_ or `unit tests <http://en.wikipedia.org/wiki/Unit_testing>`_ seem
adequate:

    * Integration tests are too difficult to integrate in your test harness due to automation issues, permissions or
      plain lack of performance.
    * Unit tests are too difficult to write due to design issues (like too many dependencies, dependency injects is too
      hard etc) or take too much time to write to get good code coverage.

The :obj:`Story <aspectlib.test.Story>` is the middle-ground, bringing those two types of testing closer. It allows you
to start with `integration tests` and later `mock`/`stub` with great ease all the dependencies.

.. warning::

    The :obj:`Story <aspectlib.test.Story>` is not intended to patch and mock complex libraries that keep state around.
    E.g.: `requests <https://pypi.python.org/pypi/requests>`_ keeps a connection pool around - there are `better
    <https://pypi.python.org/pypi/httmock>`_ `choices <https://pypi.python.org/pypi/requests-testadapter>`_.

.. note::

    Using the :obj:`Story <aspectlib.test.Story>` on imperative, stateless interfaces is best.

An example: mocking out an external system
------------------------------------------

Suppose we implement this simple GNU ``tree`` clone::

    >>> import os
    >>> def tree(root, prefix=''):
    ...     if not prefix:
    ...         print("%s%s" % (prefix, os.path.basename(root)))
    ...     for pos, name in reversed(list(enumerate(sorted(os.listdir(root), reverse=True)))):
    ...         print("%s%s%s" % (prefix, "├── " if pos else "└── ", name))
    ...         absname = os.path.join(root, name)
    ...         if os.path.isdir(absname):
    ...             tree(absname, prefix + ("│   " if pos else "    "))

Lets suppose we would make up some directories and files for our tests::

    >>> os.makedirs('some/test/dir')
    >>> os.makedirs('some/test/empty')
    >>> with open('some/test/dir/file.txt', 'w') as fh:
    ...     pass

And we'll assert that ``tree`` has this output::

    >>> tree('some')
    some
    └── test
        ├── dir
        │   └── file.txt
        └── empty

But now we're left with some garbage and have to clean it up::

    >>> import shutil
    >>> shutil.rmtree('some')

This is not very practical - we'll need to create many scenarios, and some are not easy to create automatically (e.g:
tests for permissions issues - not easy to change permissions from within a test).

Normally, to handle this we'd have have to manually monkey-patch the ``os`` module with various mocks or add
dependency-injection in the ``tree`` function and inject mocks. Either approach we'll leave us with very ugly code.

With dependency-injection tree would look like this::

    def tree(root, prefix='', basename=os.path.basename, listdir=os.listdir, join=os.path.join, isdir=os.path.isdir):
        ...

One could argue that this is overly explicit, and the function's design is damaged by testing concerns. What if we need
to check for permissions ? We'd have to extend the signature. And what if we forget to do that ? In some situations one
cannot afford all this (re-)engineering (e.g: legacy code, simplicity goals etc).

The :obj:`aspectlib.test.Story` is designed to solve this problem in a neat way.

We can start with some existing test data in the filesystem::

    >>> os.makedirs('some/test/dir')
    >>> os.makedirs('some/test/empty')
    >>> with open('some/test/dir/file.txt', 'w') as fh:
    ...     pass

Write an empty story and examine the output::

        >>> from aspectlib.test import Story
        >>> with Story(os, methods="^(?!error)[a-z]+$") as story:
        ...     pass
        >>> with story.replay(strict=False) as replay:
        ...     tree('some')
        some
        └── test
            ├── dir
            │   └── file.txt
            └── empty
        STORY/REPLAY DIFF:
            --- expected...
            +++ actual...
            @@ -...,0 +1,9 @@
            +os.getpid() == ...  # returns
            +os.listdir('some') == ['test']  # returns
            +os.stat('some/test') == os.stat_result((...))  # returns
            +os.listdir('some/test') == [...'dir'...]  # returns
            +os.stat('some/test/dir') == os.stat_result((...))  # returns
            +os.listdir('some/test/dir') == ['file.txt']  # returns
            +os.stat('some/test/dir/file.txt') == os.stat_result((...))  # returns
            +os.stat('some/test/empty') == os.stat_result((...))  # returns
            +os.listdir('some/test/empty') == []  # returns

..

    We can quickly get whatever we would need to put in the story with :obj:`aspectlib.test.Replay.unexpected`::

        >>> print(replay.unexpected())
        os.getpid() == ...  # returns
        os.listdir('some') == ['test']  # returns
        os.stat('some/test') == os.stat_result((...))  # returns
        os.listdir('some/test') == [...'dir'...]  # returns
        os.stat('some/test/dir') == os.stat_result((...))  # returns
        os.listdir('some/test/dir') == ['file.txt']  # returns
        os.stat('some/test/dir/file.txt') == os.stat_result((...))  # returns
        os.stat('some/test/empty') == os.stat_result((...))  # returns
        os.listdir('some/test/empty') == []  # returns
        <BLANKLINE>

Now we can remove the test directories and fill the story::

    >>> import shutil
    >>> shutil.rmtree('some')

..

    The story::

        >>> with Story(os, methods="^(?!error)[a-z]+$") as story:
        ...     os.getpid() == 13030
        ...     os.listdir('some') == ['test']
        ...     os.stat('some/test') == os.stat_result((16893, 6691875, 2049, 3, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))
        ...     os.listdir('some/test') == ['empty', 'dir']  # returns
        ...     os.stat('some/test/dir') == os.stat_result((16893, 6691876, 2049, 2, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))
        ...     os.listdir('some/test/dir') == ['file.txt']
        ...     os.stat('some/test/dir/file.txt') == os.stat_result((33204, 6691877, 2049, 1, 1000, 1000, 9, 1399131539, 1399131539, 1399131539))
        ...     os.stat('some/test/empty') == os.stat_result((16893, 6691877, 2049, 2, 1000, 1000, 4096, 1399132977, 1399132977, 1399132977))  # returns
        ...     os.listdir('some/test/empty') == []  # returns

    And the `strict` :obj:`replay <aspectlib.test.Story.replay>`::

        >>> with story.replay(proxy=False) as replay:
        ...     tree('some')
        some
        └── test
            ├── dir
            │   └── file.txt
            └── empty


If we diverge a bit from the story (or we'd have some unexpected change in the ``tree`` function) we'd get something
like this::

    >>> with Story(os, methods="^(?!error)[a-z]+$") as story:
    ...     os.getpid() == 13030
    ...     os.listdir('some') == ['test']
    ...     os.listdir('bogus') == ['some bogus directory']
    ...     os.stat('some/test') == os.stat_result((16893, 6691875, 2049, 3, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))
    ...     os.listdir('some/test') == ['empty', 'dir']  # returns
    ...     os.stat('some/test/dir') == os.stat_result((16893, 6691876, 2049, 2, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))
    ...     os.listdir('some/test/dir') == ['file.txt']
    ...     os.stat('some/test/dir/file.txt') == os.stat_result((33204, 6691877, 2049, 1, 1000, 1000, 9, 1399131539, 1399131539, 1399131539))
    ...     os.stat('some/test/empty') == os.stat_result((16893, 6691877, 2049, 2, 1000, 1000, 4096, 1399132977, 1399132977, 1399132977))  # returns
    ...     os.listdir('some/test/empty') == []  # returns
    >>> with story.replay(proxy=False) as replay:
    ...     tree('some')
    Traceback (most recent call last):
    ...
    AssertionError: --- expected...
    +++ actual...
    @@ -...,6 +1,5 @@
     os.getpid() == 13030  # returns
     os.listdir('some') == ['test']  # returns
    -os.listdir('bogus') == ['some bogus directory']  # returns
     os.stat('some/test') == os.stat_result((16893, 6691875, 2049, 3, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))  # returns
     os.listdir('some/test') == [...'dir'...]  # returns
     os.stat('some/test/dir') == os.stat_result((16893, 6691876, 2049, 2, 1000, 1000, 4096, 1399131539, 1399131539, 1399131539))  # returns
    <BLANKLINE>
