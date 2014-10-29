
from django.test import TestCase
from django.db import connection
from kuma.wiki.tasks import update_community_stats
from django.core.cache import get_cache

class UpdateCommunityStatsTests(TestCase):
    _contributors = 10

    def setUp(self):
        c = connection.cursor()

        try:
            for i in range(0, self._contributors):
                username = 'test_' + str(i)
                title = 'Test ' + str(i)
                slug = 'Test ' + str(i)

                if i % 2 == 0:
                    locale = 'en-US'
                else:
                    locale = 'pt-BR'

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
                                    0, \
                                    1, \
                                    0, \
                                    CURRENT_TIMESTAMP, \
                                    CURRENT_TIMESTAMP)"

                c.execute(insert_user)
                c.execute("SELECT LAST_INSERT_ID()")
                last_id = c.fetchone()

                try:
                    user_id = last_id[0]
                except IndexError:
                    return False

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
                                         '" + locale + "', \
                                         '<html></html>', \
                                         10, \
                                         0, \
                                         0, \
                                         0)"

                c.execute(insert_document)
                c.execute("SELECT LAST_INSERT_ID()")
                last_id = c.fetchone()

                try:
                    document_id = last_id[0]
                except IndexError:
                    return False

                insert_revision = "INSERT INTO wiki_revision ( \
                                           document_id, \
                                           summary, \
                                           content, \
                                           keywords, \
                                           created, \
                                           comment, \
                                           creator_id, \
                                           is_approved, \
                                           is_mindtouch_migration, \
                                           tags, \
                                           toc_depth \
                                       ) VALUES ( \
                                           " + str(document_id) + ", \
                                           '', \
                                           '', \
                                           '', \
                                           CURRENT_TIMESTAMP, \
                                           '', \
                                           " + str(user_id) + ", \
                                           1, \
                                           0, \
                                           '', \
                                           0 \
                                       )"
                c.execute(insert_revision)

        finally:
            c.close()

        return True

    def test_update_community_stats(self):
        update_community_stats.__call__()
        cache = get_cache('memcache')
        stats = cache.get('community_stats')
        self.assertIsNotNone(stats)
        self.assertTrue(stats.has_key('contributors'))
        self.assertTrue(stats.has_key('locales'))
        self.assertTrue(type(stats['contributors']) is long)
        self.assertTrue(type(stats['locales']) is long)
        self.assertEqual(stats['contributors'], self._contributors)
        self.assertEqual(stats['locales'], 2)

