"""pylint should detect yield and return mix inside genrators"""
__revision__ = None
def somegen():
    """this is a bad generator"""
    if True:
        yield 1
    else:
        return 2
