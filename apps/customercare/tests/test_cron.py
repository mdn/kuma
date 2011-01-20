import copy

from django.conf import settings

from mock import patch_object
from nose.tools import eq_

from customercare.cron import _filter_tweet, _get_oldest_tweet, purge_tweets
from customercare.models import Tweet
from sumo.tests import TestCase


class TwitterCronTestCase(TestCase):
    tweet_template = {
        "profile_image_url": (
            "http://a3.twimg.com/profile_images/688562959/"
            "jspeis_gmail.com_852af0c8__1__normal.jpg"),
        "created_at": "Mon, 25 Oct 2010 18:12:20 +0000",
        "from_user": "jspeis",
        "metadata": {
            "result_type": "recent",
        },
        "to_user_id": None,
        "text": "giving the Firefox 4 beta a whirl",
        "id": 28713868836,
        "from_user_id": 2385258,
        "geo": None,
        "iso_language_code": "en",
        "source": "&lt;a href=&quot;http://twitter.com/&quot;&gt;web&lt;/a&gt;"
    }

    def setUp(self):
        self.tweet = copy.deepcopy(self.tweet_template)

    def test_unfiltered(self):
        """Do not filter tweets without a reason."""
        eq_(self.tweet, _filter_tweet(self.tweet))

    def test_mentions(self):
        """Filter out mentions."""
        self.tweet['text'] = 'Hey @someone!'
        assert _filter_tweet(self.tweet) is None

    def test_replies(self):
        self.tweet['to_user_id'] = 12345
        self.tweet['text'] = '@someone Hello!'
        assert _filter_tweet(self.tweet) is None

    def test_retweets(self):
        """No retweets or 'via'"""
        self.tweet['text'] = 'RT @someone: Firefox is awesome'
        assert _filter_tweet(self.tweet) is None

        self.tweet['text'] = 'Firefox is awesome (via @someone)'
        assert _filter_tweet(self.tweet) is None

    def test_links(self):
        """Filter out tweets with links."""
        self.tweet['text'] = 'Just watching: http://youtube.com/12345 Fun!'
        assert _filter_tweet(self.tweet) is None

    def test_fx4status(self):
        """Ensure fx4status tweets are filtered out."""
        self.tweet['from_user'] = 'fx4status'
        assert _filter_tweet(self.tweet) is None


class GetOldestTweetTestCase(TestCase):
    fixtures = ['tweets.json']

    def test_get_oldest_tweet_exists(self):
        eq_(11, _get_oldest_tweet('en', 2).pk)
        eq_(4, _get_oldest_tweet('en', 0).pk)
        eq_(21, _get_oldest_tweet('en', 6).pk)

    def test_get_oldest_tweet_offset_too_big(self):
        eq_(None, _get_oldest_tweet('en', 100))

    def test_get_oldest_tweet_none_exist(self):
        eq_(None, _get_oldest_tweet('fr', 0))
        eq_(None, _get_oldest_tweet('fr', 1))
        eq_(None, _get_oldest_tweet('fr', 20))


class PurgeTweetsTestCase(TestCase):
    """Tweets are deleted for each locale."""
    fixtures = ['tweets.json']

    @patch_object(settings._wrapped, 'CC_MAX_TWEETS', 1)
    def test_purge_tweets_two_locales(self):
        purge_tweets()
        eq_(1, Tweet.objects.filter(locale='en').count())
        eq_(1, Tweet.objects.filter(locale='ro').count())

    @patch_object(settings._wrapped, 'CC_MAX_TWEETS', 3)
    def test_purge_tweets_one_locale(self):
        purge_tweets()
        eq_(3, Tweet.objects.filter(locale='en').count())
        # Does not touch Romanian tweets.
        eq_(2, Tweet.objects.filter(locale='ro').count())

    @patch_object(settings._wrapped, 'CC_MAX_TWEETS', 0)
    def test_purge_all_tweets(self):
        purge_tweets()
        eq_(0, Tweet.objects.count())
