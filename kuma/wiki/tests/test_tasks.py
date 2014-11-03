from kuma.users.tests import UserTestCase, user

from . import revision, document
from ..tasks import update_community_stats

from django.core.cache import get_cache


class UpdateCommunityStatsTests(UserTestCase):
    contributors = 10

    def setUp(self):
        super(UpdateCommunityStatsTests, self).setUp()
        self.cache = get_cache('memcache')

    def test_empty_community_stats(self):
        update_community_stats()
        stats = self.cache.get('community_stats')
        self.assertIsNone(stats)

    def test_populated_community_stats(self):
        for i in range(self.contributors):
            if i % 2 == 0:
                locale = 'en-US'
            else:
                locale = 'pt-BR'
            test_user = user(save=True)
            doc = document(save=True, locale=locale)
            revision(save=True, creator=test_user, document=doc)

        update_community_stats()
        stats = self.cache.get('community_stats')
        self.assertIsNotNone(stats)
        self.assertIn('contributors', stats)
        self.assertIn('locales', stats)
        self.assertIsInstance(stats['contributors'], long)
        self.assertIsInstance(stats['locales'], long)
        self.assertEqual(stats['contributors'], self.contributors)
        self.assertEqual(stats['locales'], 2)
