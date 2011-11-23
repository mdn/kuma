"""
Tests for the search (sphinx) app.
"""
import os
import shutil
import time
import json
import socket

from django.conf import settings
from django.contrib.sites.models import Site

import jingo
import mock
from nose import SkipTest
from nose.tools import assert_raises, eq_
from pyquery import PyQuery as pq
import test_utils
from devmo.tests import SkippedTestCase

from forums.models import Post
import search as constants
from search.clients import (WikiClient, QuestionsClient,
                            DiscussionClient, SearchError)
from search.utils import start_sphinx, stop_sphinx, reindex, crc32
from sumo.tests import LocalizingClient
from sumo.urlresolvers import reverse
from wiki.models import Document


def render(s, context):
    t = jingo.env.from_string(s)
    return t.render(**context)


class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['users.json', 'search/documents.json',
                'posts.json', 'questions.json']
    sphinx = True
    sphinx_is_running = False

    def setUp(self):
        if not SphinxTestCase.sphinx_is_running:
            if not settings.SPHINX_SEARCHD or not settings.SPHINX_INDEXER:
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            if os.path.exists(settings.TEST_SPHINX_PATH):
                shutil.rmtree(settings.TEST_SPHINX_PATH)

            os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'data'))
            os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'log'))
            os.makedirs(os.path.join(settings.TEST_SPHINX_PATH, 'etc'))

            reindex()
            start_sphinx()
            time.sleep(1)
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):
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
# * Replace magic numbers with the defined constants.

class SearchTest(SphinxTestCase):

    def setUp(self):
        super(SearchTest, self).setUp()
        self.client = LocalizingClient()

    def test_indexer(self):
        wc = WikiClient()
        results = wc.query('audio')
        eq_(2, len(results))

    def test_content(self):
        """Ensure template is rendered with no errors for a common search"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': constants.WHERE_WIKI})
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
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': constants.WHERE_WIKI})
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
        eq_(2, json.loads(response.content)['total'])

    def test_search_metrics(self):
        """Ensure that query strings are added to search results"""
        response = self.client.get(reverse('search'), {'q': 'audio', 'w': constants.WHERE_WIKI})
        doc = pq(response.content)
        assert doc('a.title:first').attr('href').endswith('?s=audio&as=s')

    def test_category(self):
        wc = WikiClient()
        results = wc.query('', ({'filter': 'category', 'value': [10]},))
        eq_(4, len(results))
        results = wc.query('', ({'filter': 'category', 'value': [30]},))
        eq_(1, len(results))

    def test_category_exclude(self):
        q = {'q': 'audio', 'format': 'json', 'w': constants.WHERE_WIKI}
        response = self.client.get(reverse('search'), q)
        eq_(2, json.loads(response.content)['total'])

        q = {'q': 'audio', 'category': -10, 'format': 'json', 'w': constants.WHERE_WIKI}
        response = self.client.get(reverse('search'), q)
        eq_(0, json.loads(response.content)['total'])

    def test_category_invalid(self):
        qs = {'a': 1, 'w': constants.WHERE_WIKI, 'format': 'json', 'category': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(2, json.loads(response.content)['total'])

    def test_no_filter(self):
        """Test searching with no filters."""
        wc = WikiClient()

        results = wc.query('')
        eq_(5, len(results))

    def test_firefox_filter(self):
        """Filtering by Firefox version."""
        qs = {'a': 1, 'w': constants.WHERE_WIKI, 'format': 'json'}

        qs.update({'fx': [1]})
        response = self.client.get(reverse('search'), qs)
        eq_(1, json.loads(response.content)['total'])

        qs.update({'fx': [1, 4]})
        response = self.client.get(reverse('search'), qs)
        eq_(2, json.loads(response.content)['total'])

    def test_os_filter(self):
        """Filtering by operating system."""
        qs = {'a': 1, 'w': constants.WHERE_WIKI, 'format': 'json'}

        qs.update({'os': [1]})
        response = self.client.get(reverse('search'), qs)
        eq_(1, json.loads(response.content)['total'])

        qs.update({'os': [1, 5]})
        response = self.client.get(reverse('search'), qs)
        eq_(2, json.loads(response.content)['total'])

    def test_translations_inherit_fx_values(self):
        wc = WikiClient()
        filters = [{'filter': 'locale', 'value': (crc32('fr'),)},
                   {'filter': 'fx', 'value': (1,)}]
        results = wc.query('', filters)
        eq_(1, len(results))
        eq_(4, results[0]['id'])

        filters[1]['value'] = (4,)
        results = wc.query('', filters)
        eq_(0, len(results))

    def test_translations_inherit_os_values(self):
        wc = WikiClient()
        filters = [{'filter': 'locale', 'value': (crc32('fr'),)},
                   {'filter': 'os', 'value': (1,)}]
        results = wc.query('', filters)
        eq_(1, len(results))
        eq_(4, results[0]['id'])

        filters[1]['value'] = (4,)
        results = wc.query('', filters)
        eq_(0, len(results))

    def test_range_filter(self):
        """Test filtering on a range."""
        wc = WikiClient()
        filter_ = ({'filter': 'updated',
                    'max': 1285765791,
                    'min': 1284664176,
                    'range': True},)
        results = wc.query('', filter_)
        eq_(2, len(results))

    def test_sort_mode(self):
        raise SkipTest()
        """Test set_sort_mode()."""
        # Initialize client and attrs.
        qc = QuestionsClient()
        test_for = ('updated', 'created', 'replies')

        i = 0
        for sort_mode in constants.SORT_QUESTIONS[1:]:  # Skip default sorting.
            qc.set_sort_mode(sort_mode[0], sort_mode[1])
            results = qc.query('')
            eq_(4, len(results))

            # Compare first and second.
            x = results[0]['attrs'][test_for[i]]
            y = results[1]['attrs'][test_for[i]]
            assert x > y, '%s !> %s' % (x, y)
            i += 1

    def test_created(self):
        """Basic functionality of created filter."""
        raise SkipTest('created filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json',
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

    def test_sortby_invalid(self):
        qs = {'a': 1, 'w': constants.WHERE_WIKI, 'format': 'json', 'sortby': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_invalid(self):
        """Invalid created_date is ignored."""
        raise SkipTest('created filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json',
              'created': 1, 'created_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(5, json.loads(response.content)['total'])

    def test_created_nonexistent(self):
        """created is set while created_date is left out of the query."""
        raise SkipTest('created filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json', 'created': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_created_range_sanity(self):
        """Ensure that the created_date range is sane."""
        raise SkipTest('created filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'q': 'contribute', 'created': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'created_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_updated(self):
        """Basic functionality of updated filter."""
        raise SkipTest('updated filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json',
              'sortby': 1, 'updated_date': '06/20/2010'}
        updated_vals = (
            (constants.INTERVAL_BEFORE, '/4'),
            (constants.INTERVAL_AFTER, '/2'),
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
        raise SkipTest('updated filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json',
              'updated': constants.INTERVAL_BEFORE, 'updated_date': 'invalid'}
        response = self.client.get(reverse('search'), qs)
        eq_(4, json.loads(response.content)['total'])

    def test_updated_nonexistent(self):
        """updated is set while updated_date is left out of the query."""
        raise SkipTest('updated filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json', 'updated': 1}
        response = self.client.get(reverse('search'), qs)
        eq_(response.status_code, 200)

    def test_updated_range_sanity(self):
        """Ensure that the updated_date range is sane."""
        raise SkipTest('updated filter is only for questions and forums')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'q': 'contribute', 'updated': '2',
              'format': 'json'}
        date_vals = ('05/28/2099', '05/28/1900', '05/28/1920')
        for date_ in date_vals:
            qs.update({'updated_date': date_})
            response = self.client.get(reverse('search'), qs)
            eq_(0, json.loads(response.content)['total'])

    def test_tags(self):
        """Search for tags, includes multiple."""
        qs = {'a': 1, 'w': constants.WHERE_WIKI, 'format': 'json'}
        tags_vals = (
            ('doesnotexist', 0),
            ('extant', 2),
            ('tagged', 1),
            ('extant tagged', 1),
        )

        for tag_string, total in tags_vals:
            qs.update({'tags': tag_string})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])

    def test_unicode_excerpt(self):
        """Unicode characters in the excerpt should not be a problem."""
        wc = WikiClient()
        page = Document.objects.get(pk=2)
        try:
            excerpt = wc.excerpt(page.html, u'\u3068')
            render('{{ c }}', {'c': excerpt})
        except UnicodeDecodeError:
            self.fail('Raised UnicodeDecodeError.')

    def test_utf8_excerpt(self):
        """Characters should stay in UTF-8."""
        wc = WikiClient()
        page = Document.objects.get(pk=4)
        q = u'fa\xe7on'
        excerpt = wc.excerpt(page.html, q)
        assert q in excerpt, u'%s not in %s' % (q, excerpt)

    def test_clean_excerpt(self):
        """SearchClient.excerpt() should not allow disallowed HTML through."""
        wc = WikiClient()  # Index strips HTML
        input = 'test <div>the start of something</div>'
        output_strip = '<b>test</b>  the start of something'
        eq_(output_strip, wc.excerpt(input, 'test'))

    def test_empty_content_excerpt(self):
        """SearchClient.excerpt() returns empty string for empty content."""
        wc = WikiClient()
        eq_('', wc.excerpt('', 'test'))

    def test_none_content_excerpt(self):
        """SearchClient.excerpt() returns empty string for None type."""
        wc = WikiClient()
        eq_('', wc.excerpt(None, 'test'))

    def test_wiki_index_keywords(self):
        """The keywords field of a revision is indexed."""
        wc = WikiClient()
        results = wc.query('foobar')
        eq_(1, len(results))
        eq_(3, results[0]['id'])

    def test_wiki_index_summary(self):
        """The summary field of a revision is indexed."""
        wc = WikiClient()
        results = wc.query('whatever')
        eq_(1, len(results))
        eq_(3, results[0]['id'])

    def test_wiki_index_content(self):
        """Obviously the content should be indexed."""
        wc = WikiClient()
        results = wc.query('video')
        eq_(1, len(results))
        eq_(1, results[0]['id'])

    def test_wiki_index_strip_html(self):
        """HTML should be stripped, not indexed."""
        wc = WikiClient()
        results = wc.query('strong')
        eq_(0, len(results))

    def test_ngram_chars(self):
        """Ideographs are handled correctly."""
        wc = WikiClient()
        results = wc.query(u'\u30c1')
        eq_(1, len(results))
        eq_(2, results[0]['id'])

    def test_no_syntax_error(self):
        """Test that special chars cannot cause a syntax error."""
        wc = WikiClient()
        results = wc.query('video^$')
        eq_(1, len(results))

        results = wc.query('video^^^$$$^')
        eq_(1, len(results))

    def test_no_redirects(self):
        """Redirect articles should never appear in search results."""
        wc = WikiClient()
        results = wc.query('ghosts')
        eq_(1, len(results))

    @mock.patch_object(Site.objects, 'get_current')
    def test_suggestions(self, get_current):
        """Suggestions API is well-formatted."""
        get_current.return_value.domain = 'testserver'

        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'),
                                   {'q': 'audio'})
        eq_(200, response.status_code)
        eq_('application/x-suggestions+json', response['content-type'])
        results = json.loads(response.content)
        eq_('audio', results[0])
        eq_(2, len(results[1]))
        eq_(0, len(results[2]))
        eq_(2, len(results[3]))

    @mock.patch_object(Site.objects, 'get_current')
    def test_invalid_suggestions(self, get_current):
        """The suggestions API needs a query term."""
        get_current.return_value.domain = 'testserver'
        response = self.client.get(reverse('search.suggestions',
                                           locale='en-US'))
        eq_(400, response.status_code)
        assert not response.content


class QuestionTestCase(SkippedTestCase):

    def test_num_voted_none(self):
        raise SkipTest('num_voted only applies to questions')
        qs = {'q': '', 'w': constants.WHERE_SUPPORT, 'a': 1, 'num_voted': 2, 'num_votes': ''}
        response = self.client.get(reverse('search'), qs)
        eq_(200, response.status_code)

    def test_asked_by(self):
        """Check several author values, including test for (anon)"""
        raise SkipTest('asked_by filter is only for questions')

        qs = {'a': 1, 'w': constants.WHERE_SUPPORT, 'format': 'json'}
        author_vals = (
            ('DoesNotExist', 0),
            ('jsocol', 2),
            ('pcraciunoiu', 2),
        )

        for author, total in author_vals:
            qs.update({'asked_by': author})
            response = self.client.get(reverse('search'), qs)
            eq_(total, json.loads(response.content)['total'])


class DiscussionTestCase(SkippedTestCase):

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
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json'}
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
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json'}
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
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json', 'thread_type': 1, 'forum': 1}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Sticky Thread', result['title'])

    def test_discussion_filter_locked(self):
        """Filter for locked threads."""
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json', 'thread_type': 2,
              'forum': 1, 'q': 'locked'}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Thread', result['title'])

    def test_discussion_filter_sticky_locked(self):
        """Filter for locked and sticky threads."""
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json', 'thread_type': (1, 2)}
        response = self.client.get(reverse('search'), qs)
        result = json.loads(response.content)['results'][0]
        eq_(u'Locked Sticky Thread', result['title'])

    def test_discussion_filter_created(self):
        """Filter for created date."""
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json',
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
        qs = {'a': 1, 'w': constants.WHERE_DISCUSSION, 'format': 'json',
              'sortby': 1, 'updated_date': '05/04/2010'}
        updated_vals = (
            (1, '/1'),
            (2, '/4'),
        )

        for updated, url_id in updated_vals:
            qs.update({'updated': updated})
            response = self.client.get(reverse('search'), qs)
            result = json.loads(response.content)['results'][0]
            url_end = result['url'].endswith(url_id)
            assert url_end, ('URL was "%s", expected to end with "%s"' %
                             (result['url'], url_id))

    def test_discussion_sort_mode(self):
        """Test set groupsort."""
        # Initialize client and attrs.
        dc = DiscussionClient()
        test_for = ('updated', 'created', 'replies')

        i = 0
        for groupsort in constants.GROUPSORT[1:]:  # Skip default sorting.
            dc.groupsort = groupsort
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
