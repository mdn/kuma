from django.http import HttpResponsePermanentRedirect

from django.test import RequestFactory
from nose.plugins.skip import SkipTest
from nose.tools import eq_
import test_utils

from sumo.middleware import PlusToSpaceMiddleware
from sumo.urlresolvers import get_best_language


class TrailingSlashMiddlewareTestCase(test_utils.TestCase):
    def test_no_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez')
        eq_(response.status_code, 404)

    def test_404_trailing_slash(self):
        response = self.client.get(u'/en-US/ohnoez/')
        eq_(response.status_code, 404)

    def test_remove_trailing_slash(self):
        response = self.client.get(u'/en-US/docs/files/?xxx=\xc3')
        eq_(response.status_code, 301)
        assert response['Location'].endswith('/en-US/docs/files?xxx=%C3%83')


class PlusToSpaceTestCase(test_utils.TestCase):
    rf = RequestFactory()
    ptsm = PlusToSpaceMiddleware()

    def test_plus_to_space(self):
        """Pluses should be converted to %20."""
        request = self.rf.get('/url+with+plus')
        response = self.ptsm.process_request(request)
        assert isinstance(response, HttpResponsePermanentRedirect)
        eq_('/url%20with%20plus', response['location'])

    def test_query_string(self):
        """Query strings should be maintained."""
        request = self.rf.get('/pa+th', {'a': 'b'})
        response = self.ptsm.process_request(request)
        eq_('/pa%20th?a=b', response['location'])

    def test_query_string_unaffected(self):
        """Pluses in query strings are not affected."""
        request = self.rf.get('/pa+th?var=a+b')
        response = self.ptsm.process_request(request)
        eq_('/pa%20th?var=a+b', response['location'])

    def test_pass_through(self):
        """URLs without a + should be left alone."""
        request = self.rf.get('/path')
        assert not self.ptsm.process_request(request)

    def test_with_locale(self):
        """URLs with a locale should keep it."""
        request = self.rf.get('/pa+th', {'a': 'b'})
        request.locale = 'ru'
        response = self.ptsm.process_request(request)
        eq_('/ru/pa%20th?a=b', response['location'])

    def test_smart_query_string(self):
        """The request QUERY_STRING might not be unicode."""
        request = self.rf.get(u'/pa+th')
        request.locale = 'ja'
        request.META['QUERY_STRING'] = 's=\xe3\x82\xa2'
        response = self.ptsm.process_request(request)
        eq_('/ja/pa%20th?s=%E3%82%A2', response['location'])


class BestLanguageTests(test_utils.TestCase):
    def test_english_only(self):
        """Any way you slice it, this should be 'en-US'."""
        best = get_best_language('en-US, en;q=0.5')
        eq_('en-US', best)

    def test_exact_match_language(self):
        """Exact match of a locale with only a language subtag."""
        best = get_best_language('fr, en-US;q=0.5')
        eq_('fr', best)

    def test_exact_match_region(self):
        """Exact match of a locale with language and region subtags."""
        best = get_best_language('pt-BR, en-US;q=0.5')
        eq_('pt-BR', best)

    def test_english_alias(self):
        """Our canonical English locale is 'en-US'."""
        best = get_best_language('en, fr;q=0.5')
        eq_('en-US', best)

    def test_overspecific_alias(self):
        """Our Irish locale is 'ga-IE'."""
        best = get_best_language('ga, fr;q=0.5')
        eq_('ga-IE', best)

    def test_prefix_alias(self):
        """A generic request for Portuguese should go to 'pt-PT'."""
        best = get_best_language('pt, fr;q=0.5')
        eq_('pt-PT', best)

    def test_nonprefix_alias(self):
        """We only have a single Norwegian locale."""
        raise SkipTest("Figure out what's up with the Norwegian locales")
        best = get_best_language('nn-NO, nb-NO;q=0.7, fr;q=0.3')
        eq_('no', best)

    def test_script_alias(self):
        """Our traditional Chinese locale is 'zh-TW'."""
        best = get_best_language('zh-Hant, fr;q=0.5')
        eq_('zh-TW', best)

    def test_non_existent(self):
        """If we don't have any matches, return false."""
        best = get_best_language('qaz-ZZ, qaz;q=0.5')
        eq_(False, best)

    def test_second_choice(self):
        """Respect the user's preferences during the first pass."""
        best = get_best_language('fr-FR, de;q=0.5')
        eq_('de', best)

    def test_prefix_fallback(self):
        """No matches during the first pass. Fall back to prefix."""
        best = get_best_language('fr-FR, de-DE;q=0.5')
        eq_('fr', best)

    def test_english_fallback(self):
        """Fall back to our canonical English locale, 'en-US'."""
        best = get_best_language('en-GB, fr-FR;q=0.5')
        eq_('en-US', best)

    def test_non_existent_fallback(self):
        """Respect user's preferences as much as possible."""
        best = get_best_language('qaz-ZZ, fr-FR;q=0.5')
        eq_('fr', best)
