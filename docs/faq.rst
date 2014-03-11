Frequently asked questions
==========================

Why is it called weave and not patch ?
--------------------------------------

Because it does more things that just patching. Depending on the *target* object it will patch and/or create one or more
subclasses and objects.

Why doesn't aspectlib implement AOP like in framework X and Y ?
---------------------------------------------------------------

Some frameworks don't resort to monkey patching but instead force the user to use ridiculous amounts of abstractions and
wrapping in order to make weaving possible. Notable example: `spring-python
<http://docs.spring.io/spring-python/1.2.x/sphinx/html/aop.html>`_.

For all intents and purposes I think it's wrong to have such high amount of boilerplate in Python.

Also, ``aspectlib`` is targeting a different stage of development: the maintenance stage - where the code is already
written and needs additional behavior, in a hurry :)

Where code is written from scratch and AOP is desired there are better choices than both ``aspectlib`` and
``spring-python``.

Why was aspectlib written ?
---------------------------

``aspectlib`` was initially written because I was tired of littering other people's code with prints and logging
statements just to fix one bug or understand how something works. ``aspectlib.debug.log`` is ``aspectlib``'s *crown
jewel*. Of course, ``aspectlib`` has other applications, see the :doc:`rationale`.
