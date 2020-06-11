from __future__ import print_function

import sys
from inspect import iscoroutinefunction
from inspect import isgenerator
from inspect import isgeneratorfunction
from logging import getLogger

from aspectlib import ExpectedGenerator
from aspectlib import Proceed
from aspectlib import Return
from aspectlib import UnacceptableAdvice
from aspectlib import mimic
from aspectlib.utils import logf

try:
    from inspect import isasyncgenfunction
except ImportError:
    isasyncgenfunction = iscoroutinefunction

logger = getLogger(__name__)
logdebug = logf(logger.debug)


def decorate_advising_asyncgenerator_py35(advising_function, cutpoint_function, bind):
    assert isasyncgenfunction(cutpoint_function) or iscoroutinefunction(cutpoint_function)

    async def advising_asyncgenerator_wrapper_py35(*args, **kwargs):
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
                        result = await gen
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
                    return advice.value
                else:
                    raise UnacceptableAdvice("Unknown advice %s" % advice)
        finally:
            advisor.close()
    return mimic(advising_asyncgenerator_wrapper_py35, cutpoint_function)


def decorate_advising_generator_py35(advising_function, cutpoint_function, bind):
    assert isgeneratorfunction(cutpoint_function)

    def advising_generator_wrapper_py35(*args, **kwargs):
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
                    return advice.value
                else:
                    raise UnacceptableAdvice("Unknown advice %s" % advice)
        finally:
            advisor.close()
    return mimic(advising_generator_wrapper_py35, cutpoint_function)
