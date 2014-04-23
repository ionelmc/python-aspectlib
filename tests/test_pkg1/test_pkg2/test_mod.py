def target():
    return


def func(*a):
    pass


def raises(*a):
    raise ValueError(a)

a = 1


class Stuff(object):
    def __init__(self, *args):
        if args == ('error',):
            raise ValueError
        self.args = args

    def meth(self):
        pass

    def mix(self, *args):
        self.meth()
        return getattr(self, 'args', ()) + args

    def raises(self, *a):
        raise ValueError(a)

    def other(self, *args):
        return ThatLONGStuf(*self.args + args)


class ThatLONGStuf(Stuff):
    pass
