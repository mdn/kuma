"""check operator use"""
#pylint: disable-msg=C0103
#pylint: disable-msg=W0104

__revision__ = 42

a = 1
a += 5
a = +a
b = ++a
++a
c = (++a) * b

a = 1
a -= 5
b = --a
b = a
--a
c = (--a) * b
