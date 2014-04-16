from __future__ import print_function


def func(arg):
    print("Got", arg, "in the real code !")

def badfunc():
    raise ValueError("boom!")
