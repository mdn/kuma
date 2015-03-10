from nose.plugins.skip import SkipTest
from nose.tools import eq_

from kuma.core.tests import KumaTestCase

from ..urlresolvers import get_best_language


class TrailingSlashMiddlewareTestCase(KumaTestCase):
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


class BestLanguageTests(KumaTestCase):
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
