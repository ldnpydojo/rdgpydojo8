from functools import wraps

def plus(diff, mult=1):
    "Decorator to modify result of a function"
    def do_plus(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            res = func(*args, **kwargs)
            return res * mult + diff
        return wrapper
    return do_plus


def report(func):
    def wrapper(*args, **kwargs):
        print '%s(*%r, **%r) =' % (func.func_name, args, kwargs),
        res = func(*args, **kwargs)
        print res
        return res
    return wrapper

@report
@plus(7, mult=2)
def foo(x):
    "Square a number"
    return x ** 2

#foo = report(plus(7, mult=2)(foo))
print foo(5)
