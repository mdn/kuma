# coding=utf-8

# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import datetime
import json

from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from sumo.urlresolvers import reverse
from wiki.tests import (TestCaseBase, document, revision, make_translation,
                       wait_add_rev)


class FeedTests(TestCaseBase):
    """Tests for the wiki feeds"""

    fixtures = ['test_users.json']

    def test_updated_translation_parent_feed(self):
        # Get the feed URL for reuse.
        feed_url = reverse('wiki.feeds.l10n_updates', locale='de',
                           args=(), kwargs={'format': 'json'})

        d1, d2 = make_translation()

        # There should be no entries in this feed yet.
        resp = self.client.get(feed_url)
        data = json.loads(resp.content)
        eq_(0, len(data))

        wait_add_rev(d1)

        # Now, there should be an item in the feed.
        resp = self.client.get(feed_url)
        data = json.loads(resp.content)
        eq_(1, len(data))
        ok_(d2.get_absolute_url() in data[0]['link'])

    def test_updated_translation_parent_feed_mod_link(self):
        d1, d2 = make_translation()
        first_rev_id = d1.current_revision.id
        wait_add_rev(d1)
        wait_add_rev(d1)

        feed_url = reverse('wiki.feeds.l10n_updates', locale='de',
                           args=(), kwargs={'format': 'rss'})
        resp = self.client.get(feed_url)
        feed = pq(resp.content)
        eq_(1, len(feed.find('item')))
        for i, item in enumerate(feed.find('item')):
            desc_text = pq(item).find('description').text()
            ok_("%s$compare?to=%s&from=%s" % (d1.slug,
                                                 d1.current_revision.id,
                                                 first_rev_id)
                in desc_text)

    def test_revisions_feed(self):
        d = document(title='HTML9')
        d.save()
        for i in xrange(1, 6):
            revision(save=True, document=d,
                         title='HTML9', comment='Revision %s' % i,
                         content="Some Content %s" % i,
                         is_approved=True,
                         created=datetime.datetime.now()\
                         + datetime.timedelta(seconds=5 * i))

        resp = self.client.get(reverse('wiki.feeds.recent_revisions',
                                       args=(), kwargs={'format': 'rss'}))
        eq_(200, resp.status_code)
        feed = pq(resp.content)
        eq_(5, len(feed.find('item')))
        for i, item in enumerate(feed.find('item')):
            desc_text = pq(item).find('description').text()
            ok_('by:</h3><p>testuser</p>' in desc_text)
            ok_('<h3>Comment:</h3><p>Revision' in desc_text)
            if "Edited" in desc_text:
                ok_('$compare?to' in desc_text)
                ok_('diff_chg' in desc_text)
            ok_('$edit' in desc_text)
            ok_('$history' in desc_text)

    def test_revisions_feed_diffs(self):
        d = document(title='HTML9')
        d.save()
        revision(save=True, document=d,
                    title='HTML9', comment='Revision 1',
                    content="First Content",
                    is_approved=True,
                    created=datetime.datetime.now())
        r = revision(save=True, document=d,
                    title='HTML9', comment='Revision 2',
                    content="First Content",
                    is_approved=True,
                    created=datetime.datetime.now() \
                        + datetime.timedelta(seconds=1),
                    tags='"some", "more", "tags"')
        r.review_tags.set(*[u'editorial'])

        resp = self.client.get(reverse('wiki.feeds.recent_revisions',
                                       args=(), kwargs={'format': 'rss'}))
        eq_(200, resp.status_code)
        feed = pq(resp.content)
        for i, item in enumerate(feed.find('item')):
            desc_text = pq(item).find('description').text()
            if "Edited" in desc_text:
                ok_('<h3>Tag changes:</h3>' in desc_text)
                ok_('<span class="diff_add" style="background-color: #afa; '
                    'text-decoration: none;">"more"<br />&nbsp;</span>'
                    in desc_text)
                ok_('<h3>Review changes:</h3>' in desc_text)
                ok_('<span class="diff_add" style="background-color: #afa; '
                    'text-decoration: none;">editorial</span>' in desc_text)

    def test_feed_locale_filter(self):
        """Documents and Revisions in feeds should be filtered by locale"""
        d1 = document(title="Doc1", locale='en-US', save=True)
        r1 = revision(document=d1, save=True)
        r1.review_tags.set('editorial')
        d1.tags.set('foobar')

        d2 = document(title="TransDoc1", locale='de', parent=d1, save=True)
        r2 = revision(document=d2, save=True)
        r2.review_tags.set('editorial')
        d2.tags.set('foobar')

        d3 = document(title="TransDoc1", locale='fr', parent=d1, save=True)
        r3 = revision(document=d3, save=True)
        r3.review_tags.set('editorial')
        d3.tags.set('foobar')

        show_alls = (False, True)
        locales = ('en-US', 'de', 'fr')
        for show_all in show_alls:
            for locale in locales:
                feed_urls = (
                    reverse('wiki.feeds.recent_revisions', locale=locale,
                            args=(), kwargs={'format': 'json'}),
                    reverse('wiki.feeds.recent_documents', locale=locale,
                            args=(), kwargs={'format': 'json'}),
                    reverse('wiki.feeds.recent_documents', locale=locale,
                            args=(), kwargs={'format': 'json',
                                             'tag': 'foobar'}),
                    reverse('wiki.feeds.list_review', locale=locale,
                            args=('json',)),
                    reverse('wiki.feeds.list_review_tag', locale=locale,
                            args=('json', 'editorial',)),
                )
                for feed_url in feed_urls:
                    if show_all:
                        feed_url = '%s?all_locales' % feed_url
                    resp = self.client.get(feed_url)
                    data = json.loads(resp.content)
                    if show_all:
                        eq_(3, len(data))
                    else:
                        eq_(1, len(data))
