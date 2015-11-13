from django.utils import six

from kuma.core.tests import KumaTestCase

from ..jobs import KumaJob


class JobsTests(KumaTestCase):

    def test_job_version(self):
        job = KumaJob()
        test_key = job.key('test')
        job.version = 2
        self.assertNotEqual(test_key, job.key('test'))


class EncodingJob(KumaJob):

    def fetch(self, spam):
        return spam


class TestCacheKeyWithDifferentEncoding(KumaTestCase):

    def setUp(self):
        self.job = EncodingJob()

    def test_unicode_and_bytestring_args(self):
        self.assertEqual(self.job.key(six.b('eggs')),
                         self.job.key(six.u('eggs')))

    def test_unicode_and_bytestring_kwargs(self):
        self.assertEqual(self.job.key(spam=six.b('eggs')),
                         self.job.key(spam=six.u('eggs')))
