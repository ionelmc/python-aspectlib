from __future__ import print_function

import sys
from inspect import isgenerator
from inspect import isgeneratorfunction
from logging import getLogger

from aspectlib import ExpectedGenerator
from aspectlib import Proceed
from aspectlib import Return
from aspectlib import UnacceptableAdvice
from aspectlib import mimic
from aspectlib.utils import logf

logger = getLogger(__name__)
logdebug = logf(logger.debug)


def decorate_advising_generator_py3(advising_function, cutpoint_function, bind):
    assert isgeneratorfunction(cutpoint_function)

    def advising_generator_wrapper_py3(*args, **kwargs):
        gen = cutpoint_function(*args, **kwargs)
        while True:
            if bind:
                advisor = advising_function(cutpoint_function, *args, **kwargs)
            else:
                advisor = advising_function(*args, **kwargs)

            if not isgenerator(advisor):
                raise ExpectedGenerator("advising_function %s did not return a generator." % advising_function)

            advice = next(advisor)
            logdebug('Got advice %r from %s', advice, advising_function)
            result = None
            if advice is Proceed or advice is None or isinstance(advice, Proceed):
                try:
                    result = next(gen)
                    advice = advisor.send(result)
                except StopIteration as e:
                    return e.value
                except BaseException:
                    advice = advisor.throw(*sys.exc_info())

            if advice is Return:
                yield result
            elif isinstance(advice, Return):
                yield advice.value
            else:
                raise UnacceptableAdvice("Unknown advice %s" % advice)
    return mimic(advising_generator_wrapper_py3, cutpoint_function)
