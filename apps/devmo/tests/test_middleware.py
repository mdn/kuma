from nose.tools import eq_
from test_utils import TestCase

from devmo.urlresolvers import get_best_language


class BestLanguageTests(TestCase):
    def test_english_only(self):
        best = get_best_language('en-us, en;q=0.8')
        eq_('en-US', best)

    def test_en_GB(self):
        """Stick with English if you can."""
        best = get_best_language('en-gb, fr;q=0.8')
        eq_('en-US', best)

    def test_not_worst_choice(self):
        """Try not to fall back to 'es' here."""
        best = get_best_language('en-gb, en;q=0.8, fr-fr;q=0.6, es;q=0.2')
        eq_('en-US', best)

    def test_fr_FR(self):
        best = get_best_language('fr-FR, es;q=0.8')
        eq_('fr', best)

    def test_non_existent(self):
        best = get_best_language('xy-YY, xy;q=0.8')
        eq_(False, best)

    def test_prefix_matching(self):
        """en-US is a better match for en-gb, es;q=0.2 than es."""
        best = get_best_language('en-gb, es;q=0.2')
        eq_('en-US', best)
