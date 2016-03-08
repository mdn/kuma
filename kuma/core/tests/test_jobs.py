from django.utils import six
from kuma.core.tests import KumaTestCase

from ..jobs import GenerationJob, KumaJob


class KumaJobTests(KumaTestCase):

    def test_key_changes_with_version(self):
        job = KumaJob()
        test_key = job.key('test')
        job.version = 2
        self.assertNotEqual(test_key, job.key('test'))


class GenerationJobTest(KumaTestCase):

    def test_generation_same(self):
        job1 = GenerationJob(generation_args=[1])
        job2 = GenerationJob(generation_args=[1])
        key1 = job1.key('test')
        key2 = job2.key('test')
        assert key1 == key2

    def test_invalidate_generation(self):
        job1 = GenerationJob()
        job2 = GenerationJob()
        key1_gen1 = job1.key('test')
        key2_gen1 = job2.key('test')
        assert key1_gen1 == key2_gen1

        job1.invalidate_generation()
        key1_gen2 = job1.key('test')
        key2_gen2 = job2.key('test')
        assert key1_gen1 != key1_gen2
        assert key1_gen2 == key2_gen2


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
