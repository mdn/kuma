class base:
    @classmethod
    def setup_class(cls):
        cls.inited = 1
    @classmethod
    def teardown_class(cls):
        cls.inited = 0
    def test1(self):
        assert self.inited
    def test2(self):
        assert self.inited

class testa(base):
    pass
class testb(base):
    pass
