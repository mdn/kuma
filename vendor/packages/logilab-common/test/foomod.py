"""fake module for logilb.common.bind's unit tests"""

__revision__ = '$Id: foomod.py,v 1.1 2005-02-15 17:06:08 adim Exp $'

VAR1 = 'var1'
VAR2 = 'var2'

def f1():
    return 'a'

def f2():
    global VAR1
    VAR1 = 'a'

def f3():
    global VAR1
    VAR1 = 'b'
