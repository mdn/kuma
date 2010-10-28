from datetime import datetime

from nose.tools import eq_

from customercare.helpers import isotime


def test_isotime():
    """Test isotime helper."""
    time = datetime(2009, 12, 25, 10, 11, 12)
    eq_(isotime(time), '2009-12-25T18:11:12Z')

    assert isotime(None) is None
