from logging import getLogger
from time import sleep

from aspectlib import Aspect

logger = getLogger(__name__)


def retry(func=None, retries=5, backoff=None, exceptions=(IOError, OSError, EOFError), cleanup=None, sleep=sleep):
    """
    Decorator that retries the call ``retries`` times if ``func`` raises ``exceptions``. Can use a ``backoff`` function
    to sleep till next retry.

    Example::

        >>>
    """
    @Aspect(bind=True)
    def Retry(cutpoint, *args, **kwargs):
        for count in range(retries + 1):
            try:
                if count and cleanup:
                    cleanup()
                yield
            except exceptions:
                if count == retries:
                    raise
                if not backoff:
                    timeout = 0
                elif isinstance(backoff, (int, float)):
                    timeout = backoff
                else:
                    timeout = backoff(count)
                logger.exception("%s(%s, %s) raised exception. %s retries left. Sleeping %s secs.",
                                 cutpoint.__name__, args, kwargs, retries - count, timeout)
                sleep(timeout)
    return Retry if func is None else Retry(func)

retry.exponential_backoff = lambda count: 2 ** count
retry.flat_backoff = lambda count: (1, 5)[count] if count < 2 else 15*2**count
