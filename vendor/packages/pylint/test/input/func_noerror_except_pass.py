"""
#3205: W0704 (except doesn't do anything) false positive if some statements
follow a "pass"
"""
__revision__ = None

try:
    A = 2
except ValueError:
    pass # pylint: disable-msg=W0107
    print A
