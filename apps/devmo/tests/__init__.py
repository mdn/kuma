from os.path import dirname

import mock

from django.conf import settings
from django.contrib.auth.models import User

import test_utils
from nose.plugins.skip import SkipTest

from dekicompat.backends import DekiUser
from devmo.models import UserProfile


APP_DIR = dirname(dirname(__file__))
USER_DOCS_ACTIVITY_FEED_XML = ('%s/fixtures/user_docs_activity_feed.xml' %
                               APP_DIR)

def create_profile():
    """Create a user, deki_user, and a profile for a test account"""
    user = User.objects.create_user('tester23', 'tester23@example.com',
                                    'trustno1')

    deki_user = DekiUser(id=0, username='tester23',
                         fullname='Tester Twentythree',
                         email='tester23@example.com',
                         gravatar='', profile_url=None)

    profile = UserProfile()
    profile.user = user
    profile.fullname = "Tester Twentythree"
    profile.title = "Spaceship Pilot"
    profile.organization = "UFO"
    profile.location = "Outer Space"
    profile.bio = "I am a freaky space alien."
    profile.irc_nickname = "ircuser"
    profile.locale = 'en-US'
    profile.timezone = 'US/Central'
    profile.save()

    return (user, deki_user, profile)


def mock_fetch_user_feed(test):
    @mock.patch('devmo.models.UserDocsActivityFeed.fetch_user_feed')
    def test_new(self, fetch_user_feed):
        doc_feed_data = open(USER_DOCS_ACTIVITY_FEED_XML, 'r').read()
        fetch_user_feed.return_value = doc_feed_data
        test(self)
    return test_new


class SkippedTestCase(test_utils.TestCase):
    def setUp(self):
        raise SkipTest()
