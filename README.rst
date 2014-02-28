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

``aspectlib`` is an aspect-oriented programming, monkey-patch and decorators library.

First, an AOP glossary, as it's too easy to get confused by terminology and most every AOP framework has different definitions:

.. list-table::

   * - **Cut-point**
     - Function that is advised.
   * - **Aspect**
     - Function (generator) yielding advices. ``aspectlib``'s Aspect is essentially just a function decorator.
   * - **Weaving**
     - Applying an *aspect* on one or more *cut-points*, in other words, decorating the *cut-point* functions 
       in-place. This is esentially just *monkey-patching*.
   * - **Advice**
     - Change that is applied on a *cut-point* by an *aspect*. Can be one of:

       * ``aspectlib.Proceed`` - just go forward with the **cut-point**
       * ``aspectlib.Proceed(*args, **kwargs)`` - go forward with different arguments
       * ``aspectlib.Return`` - return ``None`` instead of whatever the **cut-point** would return
       * ``aspectlib.Return(value)`` - return ``value`` instead of whatever the **cut-point** would return
       * ``raise exception`` - make the **cut-point** raise an exception instead
   * - **Concern**
     - Cross-cutting concern, Collection of aspects

Now repeat after me: *aspects* that are *concerned* with **logging** are *advising* some *cut-points*.
The *cut-points* don't need to care about **logging**, they just do their own business.
Does it make sense now ?

Ok, but why ??
==============

An astute programmer reading this will notice that AOP is just shameless monkey-patching in disguise. Shame 
on me for trying to trick you !

So if AOP is just fancy-pants monkey-patching, why not just monkey patch ?!

* You would need to handle yourself all different kids of patching (patching
  a module is different than patching a class, a function or a method for that matter).
  Why not let a library do all this gross patching mumbo-jumbo ?
* Writting the actual wrappers is repetitive and boring. You can't reuse wrappers
  but *you can reuse aspects* !
  
But monkey-patching is wrong !
------------------------------

Technically, only the *weaving* is monkey-patching. It's completely optional, you can use the *aspects* from 
``aspectlib`` as regular function decorators.

Otherwise, if you want the *wrong thing* done *right* ``aspectlib`` is exactly that. It should 
handle the corner cases for you and/or give you easy knobs to tune the patching process (see the 
``aspectlib.weave`` function). 

If ``aspectlib.weave`` doesn't work for your scenario please report a bug !

Implementation status
=====================

Weaving functions, methods, instances and classes is completed.

Pending:

* Whole-module weaving
* Concerns
* *Anything else?*

Requirements
============

:OS: Any
:Runtime: Python 2.6, 2.7, 3.3 or PyPy

What ?! Python 3.2, 3.1 and 3.0 are *NOT* supported ? Nope, *ewwwww* !

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

    aspectlib.weave(Client, retry)

or with different retry options (reconnect before retry)::

    aspectlib.weave(Client, retry, prepare=lambda self, *_: self.connect())

or just for one method::

    aspectlib.weave(Client.action, retry)

You can see here the advantage of having reusable retry functionality. Also, the retry handling is
decoupled from the ``Client`` class.

Validation
----------

::

    class BaseProcessor(object):
        def process_foo(self, data):
            # do some work

        def process_bar(self, data):
            # do some work

    class ValidationConcern(aspectlib.Concern):
        @aspectlib.Aspect
        def process_foo(self, data):
            # validate data
            if is_valid_foo(data):
              yield aspectlib.Proceed
            else:
              raise ValidationError()

        @aspectlib.Aspect
        def process_bar(self, data):
            # validate data
            if is_valid_bar(data):
              yield aspectlib.Proceed
            else:
              raise ValidationError()

    aspectlib.weave(BaseProcesor, ValidationConcern)

    class MyProcessor(BaseProcessor):
        def process_foo(self, data):
            # do some work

        def process_bar(self, data):
            # do some work

    # MyProcessor automatically inherits BaseProcesor's ValidationConcern

Question remains here how to implement the weaving (would probably require some metaclass gymnastics to
make the subclass inherit the aspect)

Cross class/module concerns
---------------------------

Probably not supported. Use a closure where you implement all the aspects; then weave all the cutpoints from
said closure.

Advice shortcuts
----------------

Many times you only need to give only one *advice* from an *aspect*. Why not have some sugar for the comon patterns ?

Before
``````

This::

    @aspectlib.before
    def my_aspect(*args, **kwargs):
        # CODE

is equivalent for this::

    @aspectlib.Aspect
    def my_aspect(*args, **kwargs):
        # CODE
        yield aspectlib.Proceed

After
`````

This::

    @aspectlib.after
    def my_aspect(*args, **kwargs):
        # CODE

is equivalent for this::

    @aspectlib.Aspect
    def my_aspect(*args, **kwargs):
        yield aspectlib.Proceed
        # CODE

Around
``````

This::

    @aspectlib.around
    def my_aspect(*args, **kwargs):
        # BEFORE CODE
        yield
        # AFTER CODE

is equivalent for this::

    @aspectlib.Aspect
    def my_aspect(*args, **kwargs):
        # BEFORE CODE
        yield aspectlib.Proceed
        # AFTER CODE

Debugging
---------

... those god damn sockets::

    aspectlib.weave(socket.socket, aspectlib.debugging.trace, log_stack=True, log_return_values=False)

And it would work with the even more *gross* ssl sockets (I hope :-)::

    aspectlib.weave(socket.ssl, aspectlib.debugging.trace, log_stack=True, log_return_values=False)
    # or
    aspectlib.weave(socket.wrap_ssl, aspectlib.debugging.trace, log_stack=True, log_return_values=False)

Actually, why not log everything from ``socket`` ?

::

    aspectlib.weave(socket, aspectlib.debugging.trace, log_stack=True, log_return_values=False)

Testing
-------

Mock behavior for tests::

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

Reference
=========

TODO. Keep calm and read the (test) code.
