Examples
========

Retry decorator
---------------

TODO: Make a more configurable retry decorator and add it in ``aspectlib.contrib``.

.. code-block:: python

    class Client(object):
        def __init__(self, address):
            self.address = address
            self.connect()
        def connect(self):
            # establish connection
        def action(self, data):
            # do some stuff

    def retry(retries=(1, 5, 15, 30, 60), retry_on=(IOError, OSError), prepare=None):
        assert len(retries)

        @aspectlib.Aspect
        def retry_aspect(*args, **kwargs):
            durations = retries
            while True:
                try:
                    yield aspectlib.Proceed
                    break
                except retry_on as exc:
                    if durations:
                        logging.warn(exc)
                        time.sleep(durations[0])
                        durations = durations[1:]
                        if prepare:
                            prepare(*args, **kwargs)
                    else:
                        raise

        return retry_aspect

Now patch the ``Client`` class to have the retry functionality on all its methods:

.. code-block:: python

    aspectlib.weave(Client, retry())

or with different retry options (reconnect before retry):

.. code-block:: python

    aspectlib.weave(Client, retry(prepare=lambda self, *_: self.connect())

or just for one method:

.. code-block:: python

    aspectlib.weave(Client.action, retry())

You can see here the advantage of having reusable retry functionality. Also, the retry handling is
decoupled from the ``Client`` class.

Debugging
---------

... those damn sockets:

.. code-block:: pycon

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
