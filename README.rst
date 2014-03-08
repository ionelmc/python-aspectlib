================
python-aspectlib
================

.. image:: https://secure.travis-ci.org/ionelmc/python-aspectlib.png
    :alt: Build Status
    :target: https://travis-ci.org/ionelmc/python-aspectlib

.. image:: https://coveralls.io/repos/ionelmc/python-aspectlib/badge.png?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib

.. image:: https://pypip.in/d/aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/aspectlib

.. image:: https://pypip.in/v/aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/aspectlib

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired.

Documentation
=============

Docs are hosted at readthedocs.org: `python-aspectlib docs <http://python-aspectlib.readthedocs.org/en/latest/>`_.

Implementation status
=====================

Weaving functions, methods, instances and classes is completed.

Pending:

* Whole-module weaving
* *Concerns* (see `docs/todo.rst`)

If ``aspectlib.weave`` doesn't work for your scenario please report a bug !

Requirements
============

:OS: Any
:Runtime: Python 2.6, 2.7, 3.3 or PyPy

Python 3.2, 3.1 and 3.0 are *NOT* supported (some objects are too crippled).

Examples
========

Retries
-------

::

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

Now patch the ``Client`` class to have the retry functionality on all its methods::

    aspectlib.weave(Client, retry())

or with different retry options (reconnect before retry)::

    aspectlib.weave(Client, retry(prepare=lambda self, *_: self.connect())

or just for one method::

    aspectlib.weave(Client.action, retry())

You can see here the advantage of having reusable retry functionality. Also, the retry handling is
decoupled from the ``Client`` class.

Debugging
---------

... those damn sockets::

    aspectlib.weave(socket.socket, aspectlib.debug.log)

Testing
-------

Mock behavior for tests::

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
