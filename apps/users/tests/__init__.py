from sumo.tests import LocalizingClient, TestCase

from users.models import Profile


class TestCaseBase(TestCase):
    """Base TestCase for the users app test cases."""

    def setUp(self):
        super(TestCaseBase, self).setUp()
        self.client = LocalizingClient()


def profile(user, **kwargs):
    """Return a saved profile for a given user."""
    defaults = {'user': user, 'name': 'Test K. User', 'bio': 'Some bio.',
                'website': 'http://support.mozilla.com',
                'timezone': None, 'country': 'US', 'city': 'Mountain View'}
    defaults.update(kwargs)

    p = Profile(**defaults)
    p.save()
    return p
