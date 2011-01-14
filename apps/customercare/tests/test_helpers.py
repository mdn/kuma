from datetime import datetime

from nose.tools import eq_

from customercare.helpers import isotime, round_percent
from sumo.tests import TestCase


def test_isotime():
    """Test isotime helper."""
    time = datetime(2009, 12, 25, 10, 11, 12)
    eq_(isotime(time), '2009-12-25T18:11:12Z')

    assert isotime(None) is None


class RoundPercentTests(TestCase):
    """Tests for round_percent."""
    def test_high_percent_int(self):
        eq_('90', str(round_percent(90)))

    def test_high_percent_float(self):
        eq_('90', str(round_percent(90.3456)))

    def test_low_percent_int(self):
        eq_('6.0', str(round_percent(6)))

    def test_low_percent_float(self):
        eq_('6.3', str(round_percent(6.299)))
