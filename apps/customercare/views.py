from datetime import datetime
from email.utils import parsedate, formatdate
import json
import logging
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST, require_GET

from bleach import Bleach
import jingo
import tweepy

from .models import CannedCategory, Tweet
import twitter


log = logging.getLogger('k.customercare')

bleach = Bleach()

MAX_TWEETS = 20


def _get_tweets(limit=MAX_TWEETS, max_id=None, reply_to=None):
    """
    Fetch a list of tweets.

    limit is the maximum number of tweets returned.
    max_id will only return tweets with the status ids less than the given id.
    """
    tweets = []
    q = Tweet.objects.filter(locale='en', reply_to=reply_to)
    if max_id:
        q = q.filter(tweet_id__lt=max_id)
    if limit:
        q = q[:limit]

    for tweet in q:
        data = json.loads(tweet.raw_json)

        parsed_date = parsedate(data['created_at'])
        date = datetime(*parsed_date[0:6])

        # Recursively fetch replies.
        if settings.CC_SHOW_REPLIES:
            replies = _get_tweets(limit=0, reply_to=tweet.tweet_id)
        else:
            replies = None

        tweets.append({
            'profile_img': bleach.clean(data['profile_image_url']),
            'user': bleach.clean(data['from_user']),
            'text': bleach.clean(data['text']),
            'id': int(tweet.tweet_id),
            'date': date,
            'reply_count': len(replies) if replies else 0,
            'replies': replies,
            'reply_to': tweet.reply_to,
        })
    return tweets


@require_GET
def more_tweets(request):
    """AJAX view returning a list of tweets."""
    max_id = request.GET.get('max_id')
    return jingo.render(request, 'customercare/tweets.html',
                        {'tweets': _get_tweets(max_id=max_id)})


@require_GET
@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    twitter = request.twitter

    canned_responses = CannedCategory.objects.all()

    return jingo.render(request, 'customercare/landing.html', {
        'canned_responses': canned_responses,
        'tweets': _get_tweets(),
        'authed': twitter.authed,
    })


@require_POST
@twitter.auth_required
def twitter_post(request):
    try:
        reply_to = int(request.POST.get('reply_to', ''))
    except ValueError:
        return HttpResponseBadRequest('Reply-to is empty')

    content = request.POST.get('content', '')
    if len(content) == 0:
        return HttpResponseBadRequest('Message is empty')

    if len(content) > 140:
        return HttpResponseBadRequest('Message is too long')

    try:
        result = request.twitter.api.update_status(content, reply_to)
    except tweepy.TweepError, e:
        return HttpResponseBadRequest('An error occured: %s' % e)

    # Store reply in database.

    # If tweepy's status models actually implemented a dictionary, it would
    # be too boring.
    status = dict(result.__dict__)
    author = dict(result.author.__dict__)

    # Raw JSON blob data
    raw_tweet_data = {
        'id': status['id'],
        'text': status['text'],
        'created_at': formatdate(time.mktime(
            status['created_at'].timetuple())),
        'iso_language_code': author['lang'],
        'from_user_id': author['id'],
        'from_user': author['screen_name'],
        'profile_image_url': author['profile_image_url'],
    }
    # Tweet metadata
    tweet_model_data = {
        'tweet_id': status['id'],
        'raw_json': json.dumps(raw_tweet_data),
        'locale': author['lang'],
        'created': status['created_at'],
        'reply_to': reply_to,
    }
    tweet = Tweet(**tweet_model_data)
    tweet.save()

    return HttpResponse()
