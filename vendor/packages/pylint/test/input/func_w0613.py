# pylint: disable-msg=R0903
"""test unused argument
"""

__revision__ = 1

def function(arg=1):
    """ignore arg"""


class AAAA:
    """dummy class"""

    def method(self, arg):
        """dummy method"""
        print self
    def __init__(self):
        pass

    @classmethod
    def selected(cls, *args, **kwargs):
        """called by the registry when the vobject has been selected.
        """
        return cls

    def using_inner_function(self, etype, size=1):
        """return a fake result set for a particular entity type"""
        rset = AAAA([('A',)]*size, '%s X' % etype,
                    description=[(etype,)]*size)
        def inner(row, col=0, etype=etype, req=self, rset=rset):
            """inner using all its argument"""
            # pylint: disable-msg = E1103
            return req.vreg.etype_class(etype)(req, rset, row, col)
        # pylint: disable-msg = W0201
        rset.get_entity = inner

class BBBB:
    """dummy class"""

    def __init__(self, arg):
        """Constructor with an extra parameter. Should raise a warning"""
        self.spam = 1

