================
python-aspectlib
================

Nothing is implemented yet ...


Glossary, as it's too easy to get confused by terminology:

:Concern: Cross-cutting concern, Collection of aspects
:Aspect: Function (generator) yielding advices
:Advice:
    Change that is applied in a cut-point. Can be one of:

    * ``aspectlib.proceed`` - just go forward with the cutpoint
    * ``aspectlib.proceed(*args, **kwargs)`` - go forward with different arguments
    * ``aspectlib.return_`` - return ``None`` instead of whatever the cutpoint would return
    * ``aspectlib.return_(value)`` - return ``value`` instead of whatever the cutpoint would return
    * ``aspectlib.raise_(type, value=None, tb=None)`` - raise ``value`` exception instead of returning

:Cut-point: Function that is advised

And most importantly :)

:Aspect-Oriented Programming: Fancy-pants monkey patching :)
: :  

Usecase analysis
================

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

        @aspectlib.aspect
        def retry_aspect(*args, **kwargs):
            durations = retries
            while True:
                try:
                    yield aspectlib.proceed
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

::

    aspectlib.weave(Client, retry)

or (reconnect before retry)::

    aspectlib.weave(Client.action, retry, prepare=lambda self, *_: self.connect())

Validation
----------

::

    class BaseProcessor(object):
        def process_foo(self, data):
            # do some work

        def process_bar(self, data):
            # do some work

    class ValidationConcern(aspectlib.Concern):
        @aspectlib.aspect
        def process_foo(self, data):
            # validate data

        @aspectlib.aspect
        def process_bar(self, data):
            # validate data

    aspectlib.weave(BaseProcesor, ValidationConcern)

    class MyProcessor(BaseProcessor):
        def process_foo(self, data):
            # do some work

        def process_bar(self, data):
            # do some work

    # MyProcessor automatically inherits BaseProcesor's ValidationConcern

Cross class/module concerns
---------------------------

Probably not supported. Use a closure where you implement all the aspects; then weave all the cutpoints from
said closure.

Advice shortcuts
----------------

Many times you only need to give only one *advice* from an *aspect*. Why not have some sugar for the comon patterns ?

    
