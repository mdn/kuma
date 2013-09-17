# coding=utf-8

import sys
import logging
import datetime

from django.conf import settings
from django.test.client import Client
from django.http import Http404
from django.utils.encoding import smart_str

import mock
from nose import SkipTest
from nose.tools import eq_, ok_
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from sumo.tests import LocalizingClient, post, get
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse

from . import TestCaseBase, FakeResponse

from wiki.models import (VersionMetadata, Document, Revision, Attachment,
                         DocumentZone,
                         AttachmentRevision, DocumentAttachment, TOC_DEPTH_H4)
from wiki.tests import (doc_rev, document, new_document_data, revision,
                        normalize_html, create_template_test_users)
from wiki.views import _version_groups, DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL


class DocumentZoneMiddlewareTestCase(TestCaseBase):
    fixtures = ['test_users.json']

    def setUp(self):
        super(DocumentZoneMiddlewareTestCase, self).setUp()
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

    def test_actual_wiki_url_redirect(self):
        """Ensure a request for the 'real' path to a document results in a
        redirect to the internal redirect path"""

        url = '/en-US/docs/%s?raw=1' % self.middle_doc.slug
        response = self.client.get(url, follow=False)
        eq_(302, response.status_code)
        eq_('http://testserver/en-US/ExtraWiki/Middle?raw=1', response['Location'])
