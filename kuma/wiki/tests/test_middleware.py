# -*- coding: utf-8 -*-
from django.test import RequestFactory

from kuma.core.cache import memcache
from kuma.core.tests import eq_
from kuma.users.tests import UserTestCase

from . import revision
from ..middleware import DocumentZoneMiddleware
from ..models import DocumentZone

from . import WikiTestCase


class DocumentZoneMiddlewareTestCase(UserTestCase, WikiTestCase):

    def setUp(self):
        super(DocumentZoneMiddlewareTestCase, self).setUp()
        self.rf = RequestFactory()
        memcache.clear()

        self.zone_root = 'ExtraWiki'
        self.zone_root_content = 'This is the Zone Root'

        root_rev = revision(title='ZoneRoot', slug='Zones/Root',
                            content=self.zone_root_content,
                            is_approved=True, save=True)
        self.root_doc = root_rev.document

        middle_rev = revision(title='middlePage', slug='Zones/Root/Middle',
                              content='This is a middlepage',
                              is_approved=True, save=True)
        self.middle_doc = middle_rev.document
        self.middle_doc.parent_topic = self.root_doc
        self.middle_doc.save()

        sub_rev = revision(title='SubPage', slug='Zones/Root/Middle/SubPage',
                           content='This is a subpage',
                           is_approved=True, save=True)
        self.sub_doc = sub_rev.document
        self.sub_doc.parent_topic = self.middle_doc
        self.sub_doc.save()

        self.root_zone = DocumentZone(document=self.root_doc)
        self.root_zone.url_root = self.zone_root
        self.root_zone.save()

        self.middle_zone = DocumentZone(document=self.middle_doc)
        self.middle_zone.save()

        other_rev = revision(title='otherPage', slug='otherPage',
                             content='This is an otherpage',
                             is_approved=True, save=True)
        self.other_doc = other_rev.document
        self.other_doc.save()

        self.other_zone = DocumentZone(document=self.other_doc)
        self.other_zone.url_root = ''
        self.other_zone.save()

        # One more doc, just to be sure we can have multiple blank url_roots
        onemore_rev = revision(title='onemorePage', slug='onemorePage',
                               content='This is an onemorepage',
                               is_approved=True, save=True)
        self.onemore_doc = onemore_rev.document
        self.onemore_doc.save()

        self.onemore_zone = DocumentZone(document=self.onemore_doc)
        self.onemore_zone.url_root = ''
        self.onemore_zone.save()

    def test_url_root_internal_redirect(self):
        """Ensure document zone with URL root results in internal redirect"""

        url = '/en-US/%s?raw' % self.zone_root
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)
        eq_(self.zone_root_content, response.content)

        url = '/en-US/%s/Middle/SubPage?raw' % self.zone_root
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)
        eq_(self.sub_doc.html, response.content)

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = '/en-US/%s/Middle/SubPage?raw' % 'NewRoot'
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)
        eq_(self.sub_doc.html, response.content)

    def test_actual_wiki_url_redirect(self):
        """
        Ensure a request for the 'real' path to a document results in a
        redirect to the internal redirect path
        """
        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/ExtraWiki/Middle?raw=1',
            response['Location'])

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/NewRoot/Middle?raw=1',
            response['Location'])

    def test_blank_url_root(self):
        """Ensure a blank url_root does not trigger URL remap"""
        url = '/en-US/docs/%s?raw=1' % self.other_doc.slug
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)

    def test_no_redirect(self):
        middleware = DocumentZoneMiddleware()
        for endpoint in ['$subscribe', '$files']:
            request = self.rf.post('/en-US/docs/%s%s?raw' %
                                   (self.other_doc.slug, endpoint))
            self.assertIsNone(middleware.process_request(request))

    def test_zone_url_ends_with_slash(self):
        """Ensure urls only rewrite with a '/' at the end of url_root

        bug 1189596
        """
        zone_url_root = 'Firéfox'
        zone_root_content = 'This is the Firéfox zone'

        root_rev = revision(title='Firéfox', slug='Mozilla/Firéfox',
                            content=zone_root_content,
                            is_approved=True, save=True)
        root_doc = root_rev.document

        root_zone = DocumentZone(document=root_doc)
        root_zone.url_root = zone_url_root
        root_zone.save()

        none_zone_rev = revision(title='Firéfox for iOS',
                                 slug='Mozilla/Firéfox_for_iOS',
                                 content='Page outside zone with same prefix',
                                 is_approved=True, save=True)
        non_zone_doc = none_zone_rev.document
        non_zone_doc.save()

        url = '/en-US/docs/%s' % non_zone_doc.slug
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)
