# coding=utf-8

import sys
import logging
import datetime

from django.conf import settings
from django.test.client import Client
from django.http import Http404
from django.utils.encoding import smart_str
from django.core.cache import get_cache

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from sumo.tests import LocalizingClient, post, get
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse

from . import TestCaseBase, FakeResponse

from wiki.models import (Document, Attachment, DocumentZone, SECONDARY_CACHE_ALIAS)
from wiki.tests import (doc_rev, document, new_document_data, revision,
                        normalize_html, create_template_test_users)
from wiki.views import _version_groups, DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL


class DocumentZoneMiddlewareTestCase(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentZoneMiddlewareTestCase, self).setUp()

        s_cache = get_cache(SECONDARY_CACHE_ALIAS)
        s_cache.clear()

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
        """Ensure a request for the 'real' path to a document results in a
        redirect to the internal redirect path"""

        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/ExtraWiki/Middle?raw=1', response['Location'])

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/NewRoot/Middle?raw=1', response['Location'])

    def test_blank_url_root(self):
        """Ensure a blank url_root does not trigger URL remap"""
        url = '/en-US/docs/%s?raw=1' % self.other_doc.slug
        response = self.client.get(url, follow=False)
        eq_(200, response.status_code)

    def test_reverse_rewrite(self):
        """Ensure reverse() URLs are remapped"""
        # HACK: This actually exercises code in apps/sumo/urlresolvers.py, but
        # lives here to share fixtures and such with other wiki URL remap code.
        url = reverse('wiki.document',
                      args=[self.other_doc.slug],
                      locale='en-US')
        eq_('/en-US/docs/otherPage', url)
        url = reverse('wiki.edit_document',
                      args=[self.other_doc.slug],
                      locale='en-US')
        eq_('/en-US/docs/otherPage$edit', url)

        url = reverse('wiki.document',
                      args=[self.middle_doc.slug],
                      locale='en-US')
        eq_('/en-US/ExtraWiki/Middle', url)
        url = reverse('wiki.edit_document',
                      args=[self.middle_doc.slug],
                      locale='en-US')
        eq_('/en-US/ExtraWiki/Middle$edit', url)

        url = reverse('wiki.edit_document',
                      args=[self.middle_doc.slug])
        eq_('/ExtraWiki/Middle$edit', url)

        self.root_zone.url_root = 'NewRoot'
        self.root_zone.save()

        url = reverse('wiki.edit_document',
                      args=[self.middle_doc.slug])
        eq_('/NewRoot/Middle$edit', url)
