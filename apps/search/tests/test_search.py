"""
Tests for the search (sphinx) app.
"""
import os
import shutil
import time
import json
import socket

from django.db import connection

import mock
from nose import SkipTest
from nose.tools import assert_raises, eq_
import test_utils
import jingo
from pyquery import PyQuery as pq

from manage import settings
from sumo.urlresolvers import reverse
import search as constants
from search.utils import start_sphinx, stop_sphinx, reindex, crc32
from search.clients import (WikiClient, QuestionsClient,
                            DiscussionClient, SearchError)
from sumo.models import WikiPage
from sumo.tests import LocalizingClient
from forums.models import Post


def render(s, context):
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

    fixtures = ['pages.json', 'categories.json', 'users.json',
                'posts.json', 'questions.json']
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


def test_sphinx_down():
    """
    Tests that the client times out when Sphinx is down.
    """
    wc = WikiClient()
    wc.sphinx.SetServer('localhost', 65535)
    assert_raises(SearchError, wc.query, 'test')


# TODO(jsocol):
# * Add tests for all Questions filters.
# * Fix skipped tests.
# * Replace magic numbers with the defined constants.

class SearchTest(SphinxTestCase):

    def setUp(self):
        super(SearchTest, self).setUp()
        self.client = LocalizingClient()

    def test_indexer(self):
        wc = WikiClient()
        results = wc.query('practice')
        eq_(2, len(results))

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_search_type_param(self):
        """Ensure that invalid values for search type (a=)
        does not cause errors"""
        response = self.client.get(reverse('search'), {'a': 'dontdie'})
        eq_('text/html; charset=utf-8', response['Content-Type'])
        eq_(200, response.status_code)

    def test_headers(self):
        """Verify caching headers of search forms and search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response
        response = self.client.get(reverse('search'))
        eq_('max-age=%s' % (settings.SEARCH_CACHE_PERIOD * 60),
            response['Cache-Control'])
        assert 'Expires' in response

    def test_page_invalid(self):
        """Ensure non-integer param doesn't throw exception."""
        qs = {'a': 1, 'format': 'json', 'page': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)
        eq_(5, json.loads(response.content)['total'])

    def test_search_metrics(self):
        """Ensure that query strings are added to search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': 3})
        doc = pq(response.content)
        assert doc('a.title:first').attr('href').endswith('?s=audio&as=s')

    def test_category(self):
        wc = WikiClient()
        results = wc.query('', ({'filter': 'category', 'value': [13]},))
        eq_(1, len(results))

    def test_category_exclude(self):

        # TODO(jsocol): Finish cleaning up these tests/fixtures.
        raise SkipTest

        response = self.client.get(reverse('search'),
                                   {'q': 'block', 'format': 'json', 'w': 3})
        eq_(2, json.loads(response.content)['total'])

        response = self.client.get(reverse('search'),
                                   {'q': 'forum', 'category': -13,
                                    'format': 'json', 'w': 1})
        eq_(1, json.loads(response.content)['total'])

    def test_category_invalid(self):
        qs = {'a': 1, 'w': 3, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(5, json.loads(response.content)['total'])

    def test_no_filter(self):
        """Test searching with no filters."""
        wc = WikiClient()

        results = wc.query('')
        eq_(10, len(results))

    def test_range_filter(self):
        """Test filtering on a range."""
        wc = WikiClient()
        filter_ = ({'filter': 'updated',
                    'max': 1244355125,
                    'min': 1244355115,
                    'range': True},)
        results = wc.query('', filter_)
        eq_(1, len(results))

    def test_search_en_locale(self):
        """Searches from the en-US locale should return documents from en."""
        qs = {'q': 'contribute', 'w': 1, 'format': 'json', 'category': 23}
        response = self.client.get(reverse('search'), qs)
        eq_(1, json.loads(response.content)['total'])

    def test_sort_mode(self):
        """Test set_sort_mode()."""

        # TODO(jsocol): Finish cleaning up these tests/fixtures.
        raise SkipTest

        # Initialize client and attrs.
        qc = QuestionsClient()
        test_for = ('updated', 'created', 'replies')

        i = 0
        for sort_mode in constants.SORT_QUESTIONS[1:]:  # Skip default sorting.
            qc.set_sort_mode(sort_mode[0], sort_mode[1])
            results = qc.query('')
            eq_(3, len(results))

            # Compare first and last.
            assert (results[0]['attrs'][test_for[i]] >
                    results[-1]['attrs'][test_for[i]])
            i += 1

    def test_num_voted_none(self):
        qs = {'q': '', 'w': 2, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created(self):
        """Basic functionality of created filter."""

        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 2, 'created_date': '06/20/2010'}
        created_vals = (
            (1, '/3'),
            (2, '/1'),
        )

        for created, url_id in created_vals:
            qs.update({'created': created})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][-1]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_created_invalid(self):
        """Invalid created_date is ignored."""
        qs = {'a': 1, 'w': 4, 'format': 'json',
              'created': 1, 'created_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(5, json.loads(response.content)['total'])

    def test_created_nonexistent(self):
        """created is set while created_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'created': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_range_sanity(self):
        """Ensure that the created_date range is sane."""
        qs = {'a': 1, 'w': '2', 'q': 'contribute', 'created': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'created_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_updated(self):
        """Basic functionality of updated filter."""
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'sortby': 1, 'updated_date': '06/20/2010'}
        updated_vals = (
            (1, '/4'),
            (2, '/2'),
        )

        for updated, url_id in updated_vals:
            qs.update({'updated': updated})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][0]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_updated_invalid(self):
        """Invalid updated_date is ignored."""
        qs = {'a': 1, 'w': 2, 'format': 'json',
              'updated': 1, 'updated_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(4, json.loads(response.content)['total'])

    def test_updated_nonexistent(self):
        """updated is set while updated_date is left out of the query."""
        qs = {'a': 1, 'w': 2, 'format': 'json', 'updated': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(response.status_code, 200)

    def test_updated_range_sanity(self):
        """Ensure that the updated_date range is sane."""
        qs = {'a': 1, 'w': '2', 'q': 'contribute', 'updated': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'updated_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_asked_by(self):
        """Check several author values, including test for (anon)"""
        qs = {'a': 1, 'w': 2, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('jsocol', 2),
            ('pcraciunoiu', 2),
        )

        for author, total in author_vals:
            qs.update({'asked_by': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

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
            eq_(total, json.loads(response.content)['total'])

    def test_unicode_excerpt(self):
        """Unicode characters in the excerpt should not be a problem."""
        wc = WikiClient()
        q = 'contribute'
        results = wc.query(q)
        eq_(1, len(results))
        page = WikiPage.objects.get(pk=results[0]['id'])
        try:
            excerpt = wc.excerpt(page.content, q)
            render('{{ c }}', {'c': excerpt})
        except UnicodeDecodeError:
            self.fail('Raised UnicodeDecodeError.')

    def test_clean_excerpt(self):
        """SearchClient.excerpt() should not allow disallowed HTML through."""
        wc = WikiClient()
        eq_('<b>test</b>&lt;/style&gt;', wc.excerpt('test</style>', 'test'))

    def test_empty_content_excerpt(self):
        """SearchClient.excerpt() returns empty string for empty content."""
        wc = WikiClient()
        eq_('', wc.excerpt('', 'test'))

    def test_none_content_excerpt(self):
        """SearchClient.excerpt() returns empty string for None type."""
        wc = WikiClient()
        eq_('', wc.excerpt(None, 'test'))

    def test_meta_tags(self):
        url_ = reverse('search')
        response = self.client.get(url_, {'q': 'contribute'})

        doc = pq(response.content)
        metas = doc('meta')
        eq_(3, len(metas))

    def test_discussion_sanity(self):
        """Sanity check for discussion forums search client."""
        dc = DiscussionClient()
        filters_f = [{'filter': 'author_ord', 'value': (crc32('admin'),)}]
        results = dc.query(u'', filters_f)
        eq_(1, len(results))
        post = Post.objects.get(pk=results[0]['id'])
        eq_(u'yet another <b>post</b>', dc.excerpt(post.content, u'post'))

    def test_discussion_filter_author(self):
        """Filter by author in discussion forums."""
        qs = {'a': 1, 'w': 4, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('admin', 1),
            ('jsocol', 4),
        )

        for author, total in author_vals:
            qs.update({'author': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_forum(self):
        """Filter by forum in discussion forums."""
        qs = {'a': 1, 'w': 4, 'format': 'json'}
        forum_vals = (
            # (forum_id, num_results)
            (1, 4),
            (2, 1),
            (3, 0),  # this forum does not exist
        )

        for forum_id, total in forum_vals:
            qs.update({'forum': forum_id})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_discussion_filter_sticky(self):
        """Filter for sticky threads."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 1, 'forum': 1}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Sticky Thread', result['title'])

    def test_discussion_filter_locked(self):
        """Filter for locked threads."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': 2,
              'forum': 1, 'q': 'locked'}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Thread', result['title'])

    def test_discussion_filter_sticky_locked(self):
        """Filter for locked and sticky threads."""
        qs = {'a': 1, 'w': 4, 'format': 'json', 'thread_type': (1, 2)}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Sticky Thread', result['title'])

    def test_discussion_filter_created(self):
        """Filter for created date."""
        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 2, 'created_date': '05/03/2010'}
        created_vals = (
            (1, '/1'),
            (2, '/5'),
        )

        for created, url_id in created_vals:
            qs.update({'created': created})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][-1]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_discussion_filter_updated(self):
        """Filter for updated date."""

        # TODO(jsocol): Finish cleaning up these tests/fixtures.
        raise SkipTest

        qs = {'a': 1, 'w': 4, 'format': 'json',
              'sortby': 1, 'updated_date': '05/03/2010'}
        updated_vals = (
            (1, '/1'),
            (2, '/4'),
        )

        for updated, url_id in updated_vals:
            qs.update({'updated': updated})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][0]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('Url was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_discussion_sort_mode(self):
        """Test set_groupsort()."""

        # TODO(jsocol): Finish cleaning up these tests/fixtures.
        raise SkipTest

        # Initialize client and attrs.
        dc = DiscussionClient()
        test_for = ('updated', 'created', 'replies')

        i = 0
        for groupsort in constants.GROUPSORT[1:]:  # Skip default sorting.
            dc.set_groupsort(groupsort)
            results = dc.query('')
            eq_(5, len(results))

            # Compare first and last.
            assert (results[0]['attrs'][test_for[i]] >
                    results[-1]['attrs'][test_for[i]])
            i += 1


query = lambda *args, **kwargs: WikiClient().query(*args, **kwargs)


@mock.patch('search.clients.WikiClient')
def test_excerpt_timeout(sphinx_mock):
    def sphinx_error(cls):
        raise cls

    sphinx_mock.query.side_effect = lambda *a: sphinx_error(socket.timeout)
    assert_raises(SearchError, query, 'xxx')

    sphinx_mock.query.side_effect = lambda *a: sphinx_error(Exception)
    assert_raises(SearchError, query, 'xxx')
