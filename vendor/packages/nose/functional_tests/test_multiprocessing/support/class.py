class TestFunctionalTest(object):
    counter = 0
    @classmethod
    def setup_class(cls):
        cls.counter += 1
    @classmethod
    def teardown_class(cls):
        cls.counter -= 1
    def _run(self):
        assert self.counter==1
    def test1(self):
        self._run()
    def test2(self):
        self._run()
