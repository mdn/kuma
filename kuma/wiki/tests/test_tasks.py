
from django.test import TestCase
from django.db import connection
from kuma.wiki.tasks import update_community_stats
from django.core.cache import get_cache

class UpdateCommunityStatsTests(TestCase):
    def populate_data(self):
        c = connection.cursor()

        try:
            for i in range(1, 6):
                username = 'test_' + str(i)
                title = 'Test ' + str(i)
                slug = 'Test ' + str(i)

                insert_user = "INSERT INTO auth_user ( \
                                    username, \
                                    first_name, \
                                    last_name, \
                                    email, \
                                    password, \
                                    is_staff, \
                                    is_active, \
                                    is_superuser, \
                                    last_login, \
                                    date_joined \
                                 ) VALUES ( \
                                    '" + username + "', \
                                    'test@email.com', \
                                    'John', \
                                    'Doe', \
                                    '!', \
                                    1, \
                                    1, \
                                    0, \
                                    CURRENT_TIMESTAMP, \
                                    CURRENT_TIMESTAMP)"

                insert_document = "INSERT INTO wiki_document ( \
                                         title, \
                                         slug, \
                                         is_template, \
                                         is_localizable, \
                                         locale, \
                                         html, \
                                         category, \
                                         defer_rendering, \
                                         is_redirect, \
                                         deleted \
                                     ) VALUES (\
                                         '" + title + "', \
                                         '" + slug + "', \
                                         0, \
                                         1, \
                                         'en-US', \
                                         '<html></html>', \
                                         10, \
                                         0, \
                                         0, \
                                         0)"

        finally:
            c.close()


    def test_update_community_stats(self):
        update_community_stats.__call__()
        cache = get_cache('memcache')
        stats = cache.get('community_stats')
        self.assertIsNotNone(stats)
        self.assertTrue(stats.has_key('contributors'))
        self.assertTrue(stats.has_key('locales'))
        self.assertTrue(type(stats['contributors']) is long)
        self.assertTrue(type(stats['locales']) is long)

