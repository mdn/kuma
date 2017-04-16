# pylint: disable-msg=C0302
"""pylint option block-disable-msg"""
__revision__ = None

class Foo(object):
    """block-disable-msg test"""
    
    def __init__(self):
        pass

    def meth1(self, arg):
        """this issues a message"""
        print self
    
    def meth2(self, arg):
        """and this one not"""
        # pylint: disable-msg=W0613
        print self\
              + "foo"

    def meth3(self):
        """test one line disabling"""
        # no error
        print self.bla # pylint: disable-msg=E1101
        # error
        print self.blop 

    def meth4(self):
        """test re-enabling"""
        # pylint: disable-msg=E1101
        # no error
        print self.bla
        print self.blop 
        # pylint: enable-msg=E1101
        # error
        print self.blip

    def meth5(self):
        """test IF sub-block re-enabling"""
        # pylint: disable-msg=E1101
        # no error
        print self.bla
        if self.blop:
            # pylint: enable-msg=E1101
            # error
            print self.blip
        else:
            # no error
            print self.blip
        # no error
        print self.blip

    def meth6(self):
        """test TRY/EXCEPT sub-block re-enabling"""
        # pylint: disable-msg=E1101
        # no error
        print self.bla
        try:
            # pylint: enable-msg=E1101
            # error
            print self.blip
        except UndefinedName: # pylint: disable-msg=E0602
            # no error
            print self.blip
        # no error
        print self.blip

    def meth7(self):
        """test one line block opening disabling"""
        if self.blop: # pylint: disable-msg=E1101
            # error
            print self.blip
        else:
            # error
            print self.blip
        # error
        print self.blip


    def meth8(self):
        """test late disabling"""
        # error
        print self.blip
        # pylint: disable-msg=E1101
        # no error
        print self.bla
        print self.blop 

    def meth9(self):
        """test re-enabling right after a block with whitespace"""
        eris = 5

        if eris:
            print ("In block")

        # pylint: disable-msg=E1101
        # no error
        print self.bla
        print self.blu
        # pylint: enable-msg=E1101
        # error
        print self.blip

class ClassLevelMessage(object):
    """shouldn't display to much attributes/not enough methods messages
    """
    # pylint: disable-msg=R0902,R0903
    
    def __init__(self):
        self.attr1 = 1
        self.attr2 = 1
        self.attr3 = 1
        self.attr4 = 1
        self.attr5 = 1
        self.attr6 = 1
        self.attr7 = 1
        self.attr8 = 1
        self.attr9 = 1
        self.attr0 = 1

    def too_complex_but_thats_ok(self, attr1, attr2):
        """THIS Method has too much branches and returns but i don't care
        """
        # pylint: disable-msg=R0912,R0911
        try:
            attr3 = attr1+attr2
        except ValueError:
            attr3 = None
        except:
            return 'duh', self
        if attr1:
            for i in attr1:
                if attr2:
                    return i
            else:
                return 'duh'
        elif attr2:
            for i in attr2:
                if attr2:
                    return i
            else:
                return 'duh'
        else:
            for i in range(15):
                if attr3:
                    return i
            else:
                return 'doh'
        return None



































































































































































































































































































































































































































































































































































































































































































































































































































































































print 'hop, too many lines but i don\'t care'
