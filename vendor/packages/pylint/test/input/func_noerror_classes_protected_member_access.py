"""
#3123: W0212 false positive on static method
"""
__revision__ = 1

class A3123:
    """oypuee"""
    _protected = 1
    def __init__(self):
        pass

    
    def cmeth(cls, val):
        """set protected member"""
        cls._protected = +val

    cmeth = classmethod(cmeth)

    def smeth(val):
        """set protected member"""
        A3123._protected += val

    smeth = staticmethod(smeth)
    
