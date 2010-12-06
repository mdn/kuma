import calendar
from datetime import datetime, timedelta
import json
import logging
import re
import rfc822
import time
import urllib
import urllib2

from django.conf import settings
from django.core.cache import cache
from django.db.utils import IntegrityError
from django.utils.encoding import smart_str

import cronjobs
import tweepy

from customercare.models import Tweet


SEARCH_URL = 'http://search.twitter.com/search.json'

LINK_REGEX = re.compile('https?\:', re.IGNORECASE)
MENTION_REGEX = re.compile('(^|\W)@')
RT_REGEX = re.compile('^rt\W', re.IGNORECASE)

log = logging.getLogger('k.twitter')


@cronjobs.register
def collect_tweets():
    """Collect new tweets about Firefox."""
    search_options = {
        'q': 'firefox',
        'rpp': settings.CC_TWEETS_PERPAGE,  # Items per page.
        'result_type': 'recent',  # Retrieve tweets by date.
    }

    # If we already have some tweets, collect nothing older than what we have.
    try:
        latest_tweet = Tweet.objects.latest()
    except Tweet.DoesNotExist:
        log.debug('No existing tweets. Retrieving %d tweets from search.' % (
            settings.CC_TWEETS_PERPAGE))
    else:
        search_options['since_id'] = latest_tweet.tweet_id
        log.debug('Retrieving tweets with id >= %s' % latest_tweet.tweet_id)

    # Retrieve Tweets
    try:
        raw_data = json.load(urllib.urlopen('%s?%s' % (
            SEARCH_URL, urllib.urlencode(search_options))))
    except Exception, e:
        log.warning('Twitter request failed: %s' % e)
        return

    if not ('results' in raw_data and raw_data['results']):
        log.info('Twitter returned 0 results.')
        return

    # Drop tweets into DB
    for item in raw_data['results']:
        log.debug('Handling tweet %d: %s...' % (item['id'],
                                                smart_str(item['text'][:50])))
        # Apply filters to tweet before saving
        item = _filter_tweet(item)
        if not item:
            continue

        created_date = datetime.utcfromtimestamp(calendar.timegm(
            rfc822.parsedate(item['created_at'])))

        item_lang = item.get('iso_language_code', 'en')
        tweet = Tweet(tweet_id=item['id'], raw_json=json.dumps(item),
                      locale=item_lang, created=created_date)
        try:
            tweet.save()
        except IntegrityError:
            continue
        else:
            log.debug('Tweet %d saved.' % item['id'])

    # When all is done, truncate list of tweets to (approx.) maximum number.
    try:
        keep_tweet = Tweet.objects.filter(
            reply_to=None)[settings.CC_MAX_TWEETS]
    except IndexError:
        pass
    else:
        log.debug('Truncating tweet list: Removing tweets older than %s.' % (
            keep_tweet.created))
        Tweet.objects.filter(created__lte=keep_tweet.created).delete()


def _filter_tweet(item):
    """
    Apply some filters to an incoming tweet.

    May modify tweet. If None is returned, tweet will be discarded.
    Used to exclude replies and such from incoming tweets.
    """
    # No replies, no mentions
    if item['to_user_id'] or MENTION_REGEX.search(item['text']):
        log.debug('Tweet %d discarded (reply).' % item['id'])
        return None

    # No retweets
    if RT_REGEX.search(item['text']) or item['text'].find('(via ') > -1:
        log.debug('Tweet %d discarded (retweet).' % item['id'])
        return None

    # No links
    if LINK_REGEX.search(item['text']):
        log.debug('Tweet %d discarded (link).' % item['id'])
        return None

    # Exclude filtered users
    if item['from_user'] in settings.CC_IGNORE_USERS:
        log.debug('Tweet %d discarded (user %s).' % (
            item['id'], item['from_user']))
        return None

    return item


@cronjobs.register
def get_customercare_stats():
    """
    Fetch Customer Care stats from Mozilla Metrics.

    Example Activity Stats data:
        {"resultset": [["Yesterday",1234,123,0.0154],
                       ["Last Week",12345,1234,0.0240], ...]
         "metadata": [...]}

    Example Top Contributor data:
        {"resultset": [[1,"Overall","John Doe","johndoe",840],
                       [2,"Overall","Jane Doe","janedoe",435], ...],
         "metadata": [...]}
    """

    stats_sources = {
        settings.CC_TWEET_ACTIVITY_URL: settings.CC_TWEET_ACTIVITY_CACHE_KEY,
        settings.CC_TOP_CONTRIB_URL: settings.CC_TOP_CONTRIB_CACHE_KEY,
    }
    for url, cache_key in stats_sources.items():
        log.debug('Updating %s from %s' % (cache_key, url))
        try:
            json_resource = urllib2.urlopen(url)
            json_data = json.load(json_resource)
            if not json_data['resultset']:
                raise KeyError('Result set was empty.')
        except Exception, e:
            log.error('Error updating %s: %s' % (cache_key, e))
            continue

        # Make sure the file is not outdated.
        headers = json_resource.info()
        lastmod = datetime.fromtimestamp(time.mktime(
            rfc822.parsedate(headers['Last-Modified'])))
        if ((datetime.now() - lastmod) > timedelta(
            seconds=settings.CC_STATS_WARNING)):
            log.warning('Resource %s is outdated. Last update: %s' % (
                cache_key, lastmod))

        # Grab top contributors' avatar URLs from the public twitter API.
        if cache_key == settings.CC_TOP_CONTRIB_CACHE_KEY:
            twitter = tweepy.API()
            avatars = {}
            for contrib in json_data['resultset']:
                username = contrib[3]

                if avatars.get(username):
                    continue

                try:
                    user = twitter.get_user(username)
                except tweepy.TweepError, e:
                    log.warning('Error grabbing avatar of user %s: %s' % (
                        username, e))
                else:
                    avatars[username] = user.profile_image_url
            json_data['avatars'] = avatars

        cache.set(cache_key, json_data, settings.CC_STATS_CACHE_TIMEOUT)
