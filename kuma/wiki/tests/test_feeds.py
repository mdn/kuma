# -*- coding: utf-8 -*-
import datetime
import json
import hashlib
import time

from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase
from . import WikiTestCase, document, revision, make_translation, wait_add_rev


class FeedTests(UserTestCase, WikiTestCase):
    """Tests for the wiki feeds"""
    localizing_client = True

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
        now = datetime.datetime.now()
        for i in xrange(1, 6):
            created = now + datetime.timedelta(seconds=5 * i)
            revision(save=True,
                     document=d,
                     title='HTML9',
                     comment='Revision %s' % i,
                     content="Some Content %s" % i,
                     is_approved=True,
                     created=created)

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

        resp = self.client.get(reverse('wiki.feeds.recent_revisions',
                                       args=(), kwargs={'format': 'rss'}) +
                               '?limit=2')
        feed = pq(resp.content)
        eq_(2, len(feed.find('item')))

        resp = self.client.get(reverse('wiki.feeds.recent_revisions',
                                       args=(), kwargs={'format': 'rss'}) +
                               '?limit=2&page=1')
        ok_('Revision 5' in resp.content)
        ok_('Revision 4' in resp.content)

        resp = self.client.get(reverse('wiki.feeds.recent_revisions',
                                       args=(), kwargs={'format': 'rss'}) +
                               '?limit=2&page=2')
        ok_('Revision 3' in resp.content)
        ok_('Revision 2' in resp.content)

    def test_bug869301_revisions_feed_locale(self):
        """Links to documents in revisions feed with ?all_locales should
        reflect proper document locale, regardless of requestor's locale"""
        d = document(title='HTML9', locale="fr")
        d.save()
        now = datetime.datetime.now()
        for i in xrange(1, 6):
            created = now + datetime.timedelta(seconds=5 * i)
            revision(save=True,
                     document=d,
                     title='HTML9',
                     comment='Revision %s' % i,
                     content="Some Content %s" % i,
                     is_approved=True,
                     created=created)

        resp = self.client.get('%s?all_locales' %
                               reverse('wiki.feeds.recent_revisions',
                                       args=(),
                                       kwargs={'format': 'rss'},
                                       locale='en-US'))
        eq_(200, resp.status_code)
        feed = pq(resp.content)
        eq_(5, len(feed.find('item')))
        for i, item in enumerate(feed.find('item')):
            href = pq(item).find('link').text()
            ok_('/fr/' in href)

    def test_revisions_feed_diffs(self):
        d = document(title='HTML9')
        d.save()
        revision(save=True,
                 document=d,
                 title='HTML9',
                 comment='Revision 1',
                 content="First Content",
                 is_approved=True,
                 created=datetime.datetime.now())
        r = revision(save=True,
                     document=d,
                     title='HTML9',
                     comment='Revision 2',
                     content="First Content",
                     is_approved=True,
                     created=(datetime.datetime.now() +
                              datetime.timedelta(seconds=1)),
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

    def test_feed_unchanged_after_render(self):
        """Rendering a document shouldn't affect feed contents, unless the
        document content has actually been changed."""
        d1 = document(title="FeedDoc1", locale='en-US', save=True)
        revision(document=d1, save=True)

        time.sleep(1)  # Let timestamps tick over.
        d2 = document(title="FeedDoc2", locale='en-US', save=True)
        revision(document=d2, save=True)

        time.sleep(1)  # Let timestamps tick over.
        d3 = document(title="FeedDoc3", locale='en-US', save=True)
        revision(document=d3, save=True)

        time.sleep(1)  # Let timestamps tick over.
        d4 = document(title="FeedDoc4", locale='en-US', save=True)
        # No r4, so we can trigger the no-current-rev edge case

        feed_url = reverse('wiki.feeds.recent_documents', locale='en-US',
                           args=(), kwargs={'format': 'rss'})

        # Force a render, hash the feed
        for d in (d1, d2, d3, d4):
            d.render(cache_control="no-cache")
        resp = self.client.get(feed_url)
        feed_hash_1 = hashlib.md5(resp.content).hexdigest()

        # Force another render, hash the feed
        time.sleep(1)  # Let timestamps tick over.
        for d in (d1, d2, d3, d4):
            d.render(cache_control="no-cache")
        resp = self.client.get(feed_url)
        feed_hash_2 = hashlib.md5(resp.content).hexdigest()

        # The hashes should match
        eq_(feed_hash_1, feed_hash_2)

        # Make a real edit.
        time.sleep(1)  # Let timestamps tick over.
        revision(document=d2, content="Hah! An edit!", save=True)
        for d in (d1, d2, d3, d4):
            d.render(cache_control="no-cache")

        # This time, the hashes should *not* match
        resp = self.client.get(feed_url)
        feed_hash_3 = hashlib.md5(resp.content).hexdigest()
        ok_(feed_hash_2 != feed_hash_3)

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
