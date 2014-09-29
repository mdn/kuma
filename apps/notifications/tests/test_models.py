import test_utils
from nose.tools import eq_

from notifications.models import WatchFilter
from notifications.tests import watch_filter


# TODO: write a test to ensure that event types don't collide
# case-insensitive-ly
# E.g. No duplicates in this list: [et.lower() for et in EVENT_TYPES]


class WatchFilterTests(test_utils.TestCase):
    """Tests for WatchFilter"""

    def test_value_range(self):
        """Assert 0 and 2**32-1 both fit in the value field.

        That's the range of our hash function.

        """
        MAX_INT = 2 ** 32 - 1
        watch_filter(name='maxint', value=MAX_INT).save()
        eq_(MAX_INT, WatchFilter.objects.get(name='maxint').value)
