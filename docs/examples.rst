Examples
========

Retrying
---------------

.. code-block:: python

    class Client(object):
        def __init__(self, address):
            self.address = address
            self.connect()
        def connect(self):
            # establish connection
        def action(self, data):
            # do some stuff

Now patch the ``Client`` class to have the retry functionality on all its methods:

.. code-block:: python

    aspectlib.weave(Client, aspectlib.contrib.retry())

or with different retry options (reconnect before retry):

.. code-block:: python

    aspectlib.weave(Client, aspectlib.contrib.retry(prepare=lambda self, *_: self.connect())

or just for one method:

.. code-block:: python

    aspectlib.weave(Client.action, aspectlib.contrib.retry())

You can see here the advantage of having reusable retry functionality. Also, the retry handling is
decoupled from the ``Client`` class.

Debugging
---------

... those damn sockets:

.. doctest:: pycon

    >>> import aspectlib, socket, sys
    >>> with aspectlib.weave(
    ...     socket.socket,
    ...     aspectlib.debug.log(
    ...         print_to=sys.stdout,
    ...         stacktrace=None,
    ...     ),
    ...     lazy=True,
    ... ):
    ...     s = socket.socket()
    ...     s.connect(('example.com', 80))
    ...     s.send(b'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
    ...     s.recv(8)
    ...     s.close()
    ...
    {socket...}.connect(('example.com', 80))
    {socket...}.connect => None
    {socket...}.send(...'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n')
    {socket...}.send => 37
    37
    {socket...}.recv(8)
    {socket...}.recv => ...HTTP/1.1...
    ...'HTTP/1.1'
    ...

The output looks a bit funky because it is written to be run by `doctest
<https://docs.python.org/2/library/doctest.html>`_ - so you don't use broken examples :)

Testing
-------

Mock behavior for tests:

.. code-block:: python

    class MyTestCase(unittest.TestCase):

        def test_stuff(self):

            @aspectlib.Aspect
            def mock_stuff(self, value):
                if value == 'special':
                    yield aspectlib.Return('mocked-result')
                else:
                    yield aspectlib.Proceed

            with aspectlib.weave(foo.Bar.stuff, mock_stuff):
                obj = foo.Bar()
                self.assertEqual(obj.stuff('special'), 'mocked-result')

Profiling
---------

There's no decorator for such in aspectlib but you can use any of the many choices on `PyPI <https://pypi.python.org/>`_.

Here's one example with `profilestats <https://pypi.python.org/pypi/profilestats>`_:

.. code-block:: pycon

    >>> import os, sys, aspectlib, profilestats
    >>> with aspectlib.weave('os.path.join', profilestats.profile(print_stats=10, dump_stats=True)):
    ...     print("os.path.join will be run with a profiler:")
    ...     os.path.join('a', 'b')
    ...
    os.path.join will be run with a profiler:
             ... function calls in ... seconds
    ...
       Ordered by: cumulative time
    ...
       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
    ...
    ...
    'a...b'

You can even mix it with the :obj:`aspectlib.debug.log` aspect:

.. code-block:: pycon

    >>> import aspectlib.debug
    >>> with aspectlib.weave('os.path.join', [profilestats.profile(print_stats=10, dump_stats=True), aspectlib.debug.log(print_to=sys.stdout)]):
    ...     print("os.path.join will be run with a profiler and aspectlib.debug.log:")
    ...     os.path.join('a', 'b')
    ...
    os.path.join will be run with a profiler and aspectlib.debug.log:
    join('a', 'b')                                                <<< ...
             ... function calls in ... seconds
    ...
       Ordered by: cumulative time
    ...
       ncalls  tottime  percall  cumtime  percall filename:lineno(function)
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
          ...    0.000    0.000    0.000    0.000 ...
    ...
    ...
    'a/b'
