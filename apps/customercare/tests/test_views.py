from nose.tools import eq_

from customercare.views import _get_tweets
from sumo.tests import TestCase


class TweetListTestCase(TestCase):
    """Tests for the customer care tweet list."""

    fixtures = ['tweets.json']

    def test_limit(self):
        """Do not return more than LIMIT tweets."""
        tweets = _get_tweets(limit=2)
        eq_(len(tweets), 2)

    def test_max_id(self):
        """Ensure max_id offset works."""
        tweets_1 = _get_tweets()
        assert tweets_1

        # Select max_id from the first list
        max_id = tweets_1[3]['id']
        tweets_2 = _get_tweets(max_id=max_id)
        assert tweets_2

        # Make sure this id is not in the result, and all tweets are older than
        # max_id.
        for tweet in tweets_2:
            assert tweet['id'] < max_id
