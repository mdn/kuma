"""
Tests for the search (sphinx) app.
"""
import os
import shutil
import time
import json
import socket

from django.test import client
from django.db import connection

import mock
from nose import SkipTest
from nose.tools import assert_raises
import test_utils
import jingo

from manage import settings
from sumo.urlresolvers import reverse
import search as constants
from search.utils import start_sphinx, stop_sphinx, reindex
from search.clients import WikiClient, ForumClient, SearchError
from sumo.models import WikiPage


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


def create_extra_tables():
    """
    Creates extra tables necessary for Sphinx indexing.

    XXX: This is the Wrong Way&trade; to do this! I'm only falling back
    to this option because I've exhausted all the other possibilities.
    This should GO AWAY when we get rid of the tiki_objects mess.
    """
    cursor = connection.cursor()

    cursor.execute('SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_freetags` (
          `tagId` int(10) unsigned NOT NULL AUTO_INCREMENT,
          `tag` varchar(30) NOT NULL DEFAULT '',
          `raw_tag` varchar(50) NOT NULL DEFAULT '',
          `lang` varchar(16) DEFAULT NULL,
          PRIMARY KEY (`tagId`)
        ) ENGINE=MyISAM AUTO_INCREMENT=12176 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_freetagged_objects` (
          `tagId` int(12) NOT NULL AUTO_INCREMENT,
          `objectId` int(11) NOT NULL DEFAULT '0',
          `user` varchar(200) NOT NULL DEFAULT '',
          `created` int(14) NOT NULL DEFAULT '0',
          PRIMARY KEY (`tagId`,`user`,`objectId`),
          KEY `tagId` (`tagId`),
          KEY `user` (`user`),
          KEY `objectId` (`objectId`)
        ) ENGINE=MyISAM AUTO_INCREMENT=12176 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_objects` (
          `objectId` int(12) NOT NULL AUTO_INCREMENT,
          `type` varchar(50) DEFAULT NULL,
          `itemId` varchar(255) DEFAULT NULL,
          `description` text,
          `created` int(14) DEFAULT NULL,
          `name` varchar(200) DEFAULT NULL,
          `href` varchar(200) DEFAULT NULL,
          `hits` int(8) DEFAULT NULL,
          PRIMARY KEY (`objectId`),
          KEY `type` (`type`,`itemId`),
          KEY `itemId` (`itemId`,`type`)
        ) ENGINE=MyISAM AUTO_INCREMENT=35581 DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_objects (objectId, type, itemId, name) VALUES
            (79, 'wiki page', 'Firefox Support Home Page',
                'Firefox Support Home Page'),
            (84, 'wiki page', 'Style Guide', 'Style Guide'),
            (62, 'wiki page', 'Video or audio does not play',
                'Video or audio does not play');
        """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS `tiki_category_objects` (
          `catObjectId` int(12) NOT NULL DEFAULT '0',
          `categId` int(12) NOT NULL DEFAULT '0',
          PRIMARY KEY (`catObjectId`,`categId`),
          KEY `categId` (`categId`)
        ) ENGINE=MyISAM DEFAULT CHARSET=latin1;
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_category_objects (catObjectId, categId) VALUES
            (79, 8), (84, 23), (62, 1), (62, 13),
            (62, 14), (62, 19), (62, 25);
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_freetags (tagId, tag, raw_tag, lang) VALUES
            (1, 'installation', 'installation', 'en'),
            (26, 'video', 'video', 'en'),
            (28, 'realplayer', 'realplayer', 'en');
        """)

    cursor.execute("""
        INSERT IGNORE INTO tiki_freetagged_objects (tagId, objectId, user,
            created) VALUES
            (1, 5, 'admin', 1185895872),
            (26, 62, 'np', 188586976),
            (28, 62, 'Vectorspace', 186155207);
        """)

    cursor.execute('SET SQL_NOTES=@OLD_SQL_NOTES;')


def destroy_extra_tables():
    """
    Removes the extra tables created by create_extra_tables.
    """

    cursor = connection.cursor()

    cursor.execute('SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;')
    cursor.execute('DROP TABLE IF EXISTS tiki_category_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_freetagged_objects')
    cursor.execute('DROP TABLE IF EXISTS tiki_freetags')
    cursor.execute('SET SQL_NOTES=@OLD_SQL_NOTES;')


class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['forums.json', 'threads.json', 'pages.json', 'categories.json']
    sphinx = True
    sphinx_is_running = False

    def setUp(self):

        create_extra_tables()

        if not SphinxTestCase.sphinx_is_running:
            if not settings.SPHINX_SEARCHD or not settings.SPHINX_INDEXER:
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            if os.path.exists('/tmp/k'):
                shutil.rmtree('/tmp/k')

            os.makedirs('/tmp/k/data')
            os.makedirs('/tmp/k/log')
            os.makedirs('/tmp/k/etc')
            reindex()
            start_sphinx()
            time.sleep(1)
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):

        destroy_extra_tables()

        if SphinxTestCase.sphinx_is_running:
            stop_sphinx()
            SphinxTestCase.sphinx_is_running = False


class SearchTest(SphinxTestCase):

    def setUp(self):
        SphinxTestCase.setUp(self)
        self.client = client.Client()

    def test_indexer(self):
        wc = WikiClient()
        results = wc.query('practice')
        self.assertNotEquals(0, len(results))

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        self.assertEquals(response['Content-Type'],
                          'text/html; charset=utf-8')
        self.assertEquals(response.status_code, 200)

    def test_category_filter(self):
        wc = WikiClient()
        results = wc.query('', ({'filter': 'category', 'value': [13]},))
        self.assertNotEquals(0, len(results))

    def test_category_exclude(self):
        response = self.client.get(reverse('search'),
                                   {'q': 'audio', 'format': 'json', 'w': 3})
        self.assertNotEquals(0, json.loads(response.content)['total'])

        response = self.client.get(reverse('search'),
                                   {'q': 'audio', 'category': -13,
                                    'format': 'json', 'w': 1})
        self.assertEquals(1, json.loads(response.content)['total'])

    def test_category_invalid(self):
        qs = {'a': 1, 'w': 3, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        self.assertNotEquals(0, json.loads(response.content)['total'])

    def test_no_filter(self):
        """Test searching with no filters."""
        wc = WikiClient()

        results = wc.query('')
        self.assertNotEquals(0, len(results))

    def test_range_filter(self):
        """Test filtering on a range."""
        wc = WikiClient()
        filter = ({'filter': 'lastmodif',
                   'max': 1244355125,
                   'min': 1244355115,
                   'range': True},)
        results = wc.query('', filter)
        self.assertEquals(1, len(results))

    def test_search_en_locale(self):
        """Searches from the en-US locale should return documents from en."""
        qs = {'q': 'contribute', 'w': 1, 'format': 'json', 'category': 23}
        response = self.client.get(reverse('search'), qs)
        self.assertNotEquals(0, json.loads(response.content)['total'])

    def test_sort_mode(self):
        """Test set_sort_mode()."""
        # Initialize client and attrs.
        fc = ForumClient()
        test_for = ('last_updated', 'created', 'replies')

        i = 0
        for sort_mode in constants.SORT[1:]:  # Skip default sorting.
            fc.set_sort_mode(sort_mode[0], sort_mode[1])
            results = fc.query('')
            self.assertNotEquals(0, len(results))

            # Compare first and last.
            self.assertTrue(results[0]['attrs'][test_for[i]] >
                            results[-1]['attrs'][test_for[i]])
            i += 1

    def test_lastmodif(self):
        qs = {'a': 1, 'w': 3, 'format': 'json', 'lastmodif': 1}
        response = self.client.get(reverse('search'), qs)
        self.assertNotEquals(0, json.loads(response.content)['total'])

    def test_created(self):
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 2, 'created_date': '10/13/2008'}
        created_vals = (
            (1, '/8288'),
            (2, '/185508'),
        )

        for created, url_id in created_vals:
            qs.update({'created': created})
            response = self.client.get(reverse('search'), qs)
            self.assertEquals(url_id, json.loads(response.content)['results']
                                          [-1]['url'][-len(url_id):])

    def test_created_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'created': 1, 'created_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        self.assertEquals(9, json.loads(response.content)['total'])

    def test_author(self):
        """Check several author values, including test for (anon)"""
        qs = {'a': 1, 'w': 2, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('Andreas Gustafsson', 1),
            ('Bob', 2),
        )

        for author, total in author_vals:
            qs.update({'author': author})
            response = self.client.get(reverse('search'), qs)
            self.assertEquals(total, json.loads(response.content)['total'])

    def test_status(self):
        qs = {'a': 1, 'w': 2, 'format': 'json'}
        status_vals = (
            (91, 8),
            (92, 2),
            (93, 1),
            (94, 2),
            (95, 1),
            (96, 3),
        )

        for status, total in status_vals:
            qs.update({'status': status})
            response = self.client.get(reverse('search'), qs)
            self.assertEquals(total, json.loads(response.content)['total'])

    def test_tags(self):
        """Search for tags, includes multiple"""
        qs = {'a': 1, 'w': 1, 'format': 'json'}
        tags_vals = (
            ('doesnotexist', 0),
            ('video', 1),
            ('realplayer video', 1),
            ('realplayer installation', 0),
        )

        for tag_string, total in tags_vals:
            qs.update({'tags': tag_string})
            response = self.client.get(reverse('search'), qs)
            self.assertEquals(total, json.loads(response.content)['total'])

    def test_unicode_excerpt(self):
        """Unicode characters in the excerpt should not be a problem."""
        wc = WikiClient()
        q = 'contribute'
        results = wc.query(q)
        self.assertNotEquals(0, len(results))
        page = WikiPage.objects.get(pk=results[0]['id'])
        try:
            excerpt = wc.excerpt(page.data, q)
            render('{{ c }}', {'c': excerpt})
        except UnicodeDecodeError:
            self.fail('Raised UnicodeDecodeError.')


def test_sphinx_down():
    """
    Tests that the client times out when Sphinx is down.
    """
    wc = WikiClient()
    assert_raises(SearchError, wc.query, 'test')


query = lambda *args, **kwargs: WikiClient().query(*args, **kwargs)

@mock.patch('search.clients.WikiClient')
def test_excerpt_timeout(sphinx_mock):
    def sphinx_error(cls):
        raise cls

    sphinx_mock.query.side_effect = lambda *a: sphinx_error(socket.timeout)
    assert_raises(SearchError, query, 'xxx')

    sphinx_mock.query.side_effect = lambda *a: sphinx_error(Exception)
    assert_raises(SearchError, query, 'xxx')
