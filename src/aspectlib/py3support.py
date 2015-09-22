from __future__ import print_function

import sys
from inspect import isgenerator
from inspect import isgeneratorfunction
from logging import getLogger

from aspectlib import ExpectedGenerator
from aspectlib import mimic
from aspectlib import Proceed
from aspectlib import Return
from aspectlib import UnacceptableAdvice
from aspectlib.utils import logf

logger = getLogger(__name__)
logdebug = logf(logger.debug)


def decorate_advising_generator_py3(advising_function, cutpoint_function, bind):
    assert isgeneratorfunction(cutpoint_function)

    def advising_generator_wrapper_py3(*args, **kwargs):
        if bind:
            advisor = advising_function(cutpoint_function, *args, **kwargs)
        else:
            advisor = advising_function(*args, **kwargs)
        if not isgenerator(advisor):
            raise ExpectedGenerator("advising_function %s did not return a generator." % advising_function)
        try:
            advice = next(advisor)
            while True:
                logdebug('Got advice %r from %s', advice, advising_function)
                if advice is Proceed or advice is None or isinstance(advice, Proceed):
                    if isinstance(advice, Proceed):
                        args = advice.args
                        kwargs = advice.kwargs
                    gen = cutpoint_function(*args, **kwargs)
                    try:
                        result = yield from gen
                    except BaseException:
                        advice = advisor.throw(*sys.exc_info())
                    else:
                        try:
                            advice = advisor.send(result)
                        except StopIteration:
                            return result
                    finally:
                        gen.close()
                elif advice is Return:
                    return
                elif isinstance(advice, Return):
                    raise StopIteration(advice.value)
                else:
                    raise UnacceptableAdvice("Unknown advice %s" % advice)
        finally:
            advisor.close()
    return mimic(advising_generator_wrapper_py3, cutpoint_function)
