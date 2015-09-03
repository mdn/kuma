from django.utils import six
from kuma.core.tests import KumaTestCase

from ..jobs import KumaJob, GenerationJob


class JobsTests(KumaTestCase):

    def test_job_version(self):
        job = KumaJob()
        test_key = job.key('test')
        job.version = 2
        self.assertNotEqual(test_key, job.key('test'))

    def test_job_generation(self):
        job = GenerationJob()
        first_gen = job.generation()
        first_gen_key = job.key('test')
        self.assertTrue(job.generation_key.endswith('generation'))
        self.assertIn(first_gen, first_gen_key)

        second_gen = job.renew()
        self.assertEqual(second_gen, job.generation())
        self.assertNotEqual(first_gen, second_gen)
        second_gen_key = job.key('test')
        self.assertNotEqual(first_gen_key, second_gen_key)


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
