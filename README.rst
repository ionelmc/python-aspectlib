================
python-aspectlib
================

.. image:: https://secure.travis-ci.org/ionelmc/python-aspectlib.png
    :alt: Build Status
    :target: http://travis-ci.org/ionelmc/python-aspectlib

.. image:: https://coveralls.io/repos/ionelmc/python-aspectlib/badge.png?branch=master
    :alt: Coverage Status
    :target: https://coveralls.io/r/ionelmc/python-aspectlib

.. image:: https://pypip.in/d/python-aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/python-aspectlib

.. image:: https://pypip.in/v/python-aspectlib/badge.png
    :alt: PYPI Package
    :target: https://pypi.python.org/pypi/python-aspectlib

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library. It is useful when changing
behavior in existing code is desired.

It as two core tools to do AOP:

.. list-table::
    :widths: 5 95

    * - ``aspectlib.Aspect``
      - An *aspect* can be created by decorating a generator with ``aspectlib.Aspect``. The generator yields *advices* -
        simple behavior changing instructions.

        The *aspect* is simple function decorator. Decorating a function with an *aspect* will change the function's
        behavior according to the *advices* yielded by the generator.

        Example::

            @aspectlib.Aspect
            def strip_return_value():
                result = yield aspectlib.Proceed
                yield aspectlib.Return(result.strip())

            @strip_return_value
            def read(name):
                return open(name).read()

        You can use these *advices*:

        * ``aspectlib.Proceed`` or ``None`` - Calls the wrapped function with the default arguments. The *yield* returns
          the function's return value or raises an exception. Can be used multiple times (will call the function
          multiple times).
        * ``aspectlib.Proceed(*args, **kwargs)`` - Same as above but with different arguments.
        * ``aspectlib.Return`` - Makes the wrapper return ``None`` instead. If ``aspectlib.Proceed`` was never used then
          the wrapped function is not called. After this the generator is closed.
        * ``aspectlib.Return(value)`` - Same as above but returns the given ``value`` instead of ``None``.
        * ``raise exception`` - Makes the wrapper raise an exception.


    * - ``aspectlib.weave``
      - Patches classes and functions with the given *aspect*. When used with a class it will patch all the methods.

        Returns an ``aspectlib.Entanglement`` object that has a ``rollback`` method and can be used a context manager.
        It will undo all the changes at the end of the context.

        ::

            @aspectlib.Aspect
            def mock_open():
                yield aspectlib.Return(StringIO("mystuff"))

            with aspectlib.weave(open, mock_open):
                assert open("/doesnt/exist.txt").read() == "mystuff"

        You can use ``aspectlib.weave`` on: classes, instances, builtin functions, module level functions, methods,
        classmethods, staticmethods, instance methods etc.

        Quick reference::

          weave(target, aspect,
                skip_magic_methods=True,
                skip_subclasses=False,
                on_init=False,
                skip_methods=(),
                only_methods=None)

        * ``target`` - A target to patch.
        * ``aspect`` - A function decorator or ``aspectlib.Aspect`` instance.
        * ``skip_magic_methods`` - Don't patch magic methods.
        * ``skip_subclasses`` - Do not patch subclasses of ``target``
        * ``on_init`` - Run the patching code from ``__init__``. This is useful when patching classes that add methods
          in ``__init__``.
        * ``skip_methods`` - List of methods to avoid patching.
        * ``only_methods`` - List of methods to patch. If ``None`` then all methods are patched.

Rationale
=========

An astute programmer reading this will notice that AOP is just shameless monkey-patching in disguise. If AOP is just
fancy-pants monkey-patching, this is why you should use ``aspectlib`` instead of making your own patching routines:

* You would need to handle yourself all different kids of patching (patching
  a module is different than patching a class, a function or a method for that matter).
  ``aspectlib`` will handle all this gross patching mumbo-jumbo for you, consistently, over many Python versions.
* Writting the actual wrappers is repetitive, boring and error-prone. You can't reuse wrappers
  but *you can reuse function decorators*.

But monkey-patching is wrong !
------------------------------

Technically, only the ``aspectlib.weave`` does monkey-patching. It's completely optional, you can ``aspectlib.Aspect``
objects as regular function decorators.

Otherwise, if you want the *wrong thing* done *right* ``aspectlib`` is exactly that. It should
handle the corner cases for you and/or give you easy knobs to tune the patching process (see the
``aspectlib.weave`` function).

If ``aspectlib.weave`` doesn't work for your scenario please report a bug !

Implementation status
=====================

Weaving functions, methods, instances and classes is completed.

Pending:

* Whole-module weaving
* *Concerns* (see `docs/todo.rst`)
* Using strings as weaving targets - so you don't have to import your targets

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
