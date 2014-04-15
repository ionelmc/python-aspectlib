def target():
    return


def func(*a):
    pass


def raises(*a):
    raise ValueError(a)

a = 1


class Stuff(object):
    def __init__(self, *args):
        self.args = args

    def meth(self):
        pass

    def mix(self, *args):
        self.meth()
        return self.args + args

    def raises(self, *a):
        raise ValueError(a)

class ThatLONGStuf(Stuff):
    pass
