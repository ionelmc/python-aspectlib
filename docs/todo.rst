TODO & Ideas
============

Validation
----------

.. code-block:: python
    :emphasize-lines: 24

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
