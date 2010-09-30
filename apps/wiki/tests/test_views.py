from nose.tools import eq_

from django.conf import settings

from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from wiki.models import VersionMetadata
from wiki.tests import doc_rev, document
from wiki.views import _version_groups


class TestVersionGroups(TestCase):
    def test_version_groups(self):
        """Make sure we correctly set up browser/version mappings for the JS"""
        versions = [VersionMetadata(1, 'Firefox 4.0', 'fx4', 5.0),
                    VersionMetadata(2, 'Firefox 3.5-3.6', 'fx35', 4.0),
                    VersionMetadata(4, 'Firefox Mobile 1.1', 'm11', 2.0)]
        want = {'fx': [(4.0, '35'), (5.0, '4')],
                'm': [(2.0, '11')]}
        eq_(want, _version_groups(versions))


class TestRedirects(TestCase):
    """Tests for the REDIRECT wiki directive"""

    fixtures = ['users.json']

    def test_redirect_suppression(self):
        """The document view shouldn't redirect when passed redirect=no."""
        redirect, _ = doc_rev('REDIRECT [[http://smoo/]]')
        response = self.client.get(
                       redirect.get_absolute_url() + '?redirect=no',
                       follow=True)
        self.assertContains(response, 'REDIRECT ')


class TestLocaleRedirects(TestCase):
    """Tests for fallbacks to en-US and such for slug lookups."""
    # Some of these may fail or be invalid if your WIKI_DEFAULT_LANGUAGE is de.

    def test_fallback_to_english(self):
        """Looking up a slug should fall back to the default locale if there
        is no match in the requested locale."""
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_doc = document(locale=en, slug='english-slug')
        en_doc.save()
        response = self.client.get(reverse('wiki.document',
                                           args=['english-slug'],
                                           locale='de'),
                                   follow=True)
        self.assertRedirects(response, en_doc.get_absolute_url())

    def test_fallback_to_translation(self):
        """If a slug isn't found in the requested locale but is in the default
        locale and if there is a translation of that default-locale document to
        the requested locale, the translation should be served."""
        en = settings.WIKI_DEFAULT_LANGUAGE
        en_doc = document(locale=en, slug='english-slug')
        en_doc.save()
        de_doc = document(locale='de', parent=en_doc)
        de_doc.save()
        response = self.client.get(reverse('wiki.document',
                                           args=['english-slug'],
                                           locale='de'),
                                   follow=True)
        self.assertRedirects(response, de_doc.get_absolute_url())
