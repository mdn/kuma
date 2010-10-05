import calendar
from datetime import datetime
import json
import logging
import re
import rfc822
import urllib

from django.conf import settings
from django.db.utils import IntegrityError
from django.utils.encoding import smart_str

import cronjobs

from .models import Tweet


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
        'rpp': settings.CC_TWEETS_PERPAGE, # Items per page.
        'result_type': 'recent', # Retrieve tweets by date.
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
        keep_tweet = Tweet.objects.all()[settings.CC_MAX_TWEETS]
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

    return item
