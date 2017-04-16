# pylint: disable-msg=C0111,R0903
"""#3291"""
__revision__ = 1

class Myarray:
    def __init__(self, array):
        self.array = array

    def __mul__(self, val):
        return Myarray(val)

    def astype(self):
        return "ASTYPE", self

def randint(maximum):
    if maximum is not None:
        return Myarray([1, 2, 3]) * 2
    else:
        return int(5)

print randint(1).astype() # we don't wan't an error for astype access
