from functools import wraps

def override_result(value):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return value
        return wrapper
    return decorator


#from collections import namedtuple
#from wrapt import decorator
#
#Call = namedtuple('Call', ('self', 'args', 'kwargs'))
#Result = namedtuple('Result', ('self', 'result', 'exception'))
#
#def record_calls(to, results=False):
#
#    @decorator
#    def recorded(func, inst, args, kwargs):
#
#        to.append(Call(inst, args, kwargs))
#        return func(*args, **kwargs)
#
#    return recorded
#
#def record_results(to):
#
#    @decorator
#    def recorded(func, inst, args, kwargs):
#        to.append((inst, args, kwargs))
#        return func(*args, **kwargs)
#
#    return recorded
#
##http://garybernhardt.github.io/python-mock-comparison/
