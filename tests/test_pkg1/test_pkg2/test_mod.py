def target():
    return

a = 1


class Stuff(object):
    def __init__(self, *args):
        self.args = args

    def meth(self):
        pass

    def mix(self, *args):
        return self.args + args
