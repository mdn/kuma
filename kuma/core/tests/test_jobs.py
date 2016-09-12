from django.utils import six
from kuma.core.tests import KumaTestCase
import mock


from ..jobs import GenerationJob, GenerationKeyJob, KumaJob


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


class GenerationKeyJobTest(KumaTestCase):
    """Test the GenerationKeyJob."""

    def setUp(self):
        self.job = GenerationKeyJob(lifetime=GenerationJob.generation_lifetime,
                                    for_class='kuma.core.GenerationJob',
                                    generation_args=['foo'])

    def test_key(self):
        assert self.job.key() == 'kuma.core.GenerationJob:foo:generation'

    @mock.patch('kuma.core.jobs.crypto.get_random_string')
    def test_fetch(self, mock_rando):
        mock_rando.return_value = 'abc123'
        assert self.job.fetch() == 'abc123'

    @mock.patch('cacheback.tasks.refresh_cache.apply_async')
    def test_refresh(self, mock_async):
        self.job.async_refresh()
        refresh_kwargs = {
            'call_args': (),
            'call_kwargs': {},
            'klass_str': 'kuma.core.jobs.GenerationKeyJob',
            'obj_args': (),
            'obj_kwargs': {
                'lifetime': self.job.lifetime,
                'for_class': self.job.for_class,
                'generation_args': self.job.generation_args},
        }
        mock_async.assert_called_once_with(kwargs=refresh_kwargs)


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
