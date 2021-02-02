from kuma.core.tests import KumaTestCase


from ..jobs import KumaJob


class KumaJobTests(KumaTestCase):
    def test_key_changes_with_version(self):
        job = KumaJob()
        test_key = job.key("test")
        job.version = 2
        self.assertNotEqual(test_key, job.key("test"))


class EncodingJob(KumaJob):
    pass


class TestCacheKeyWithDifferentEncoding(KumaTestCase):
    def setUp(self):
        self.job = EncodingJob()

    def test_unicode_and_bytestring_args(self):
        self.assertEqual(self.job.key(b"eggs"), self.job.key("eggs"))

    def test_unicode_and_bytestring_kwargs(self):
        self.assertEqual(self.job.key(spam=b"eggs"), self.job.key(spam="eggs"))
