import json

from nose.tools import eq_
import test_utils

from customercare.cron import _filter_tweet
from sumo.tests import TestCase

class TwitterCronTestCase(TestCase):
    tweet_json = """{
        "profile_image_url":"http://a3.twimg.com/profile_images/688562959/jspeis_gmail.com_852af0c8__1__normal.jpg",
        "created_at":"Mon, 25 Oct 2010 18:12:20 +0000",
        "from_user":"jspeis",
        "metadata": {"result_type":"recent"},
        "to_user_id":null,
        "text":"giving the Firefox 4 beta a whirl",
        "id":28713868836,
        "from_user_id":2385258,
        "geo":null,
        "iso_language_code":"en",
        "source":"&lt;a href=&quot;http://twitter.com/&quot;&gt;web&lt;/a&gt;"}
        """

    def setUp(self):
        self.tweet = json.loads(self.tweet_json)

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
