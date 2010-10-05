from datetime import datetime
from email.Utils import parsedate
import json
import logging

from django import http

from bleach import Bleach
import jingo
import tweepy

from .models import CannedCategory, Tweet
import twitter

log = logging.getLogger('k')

bleach = Bleach()

MAX_TWEETS = 20

def _get_tweets(limit=MAX_TWEETS):
    tweets = []
    q = Tweet.objects.filter(locale='en')
    if limit:
        q = q[:limit]

    for tweet in q:
        data = json.loads(tweet.raw_json)
        parsed_date = parsedate(data['created_at'])
        date = datetime(*parsed_date[0:6])
        tweets.append({
            'profile_img': bleach.clean(data['profile_image_url']),
            'user': bleach.clean(data['from_user']),
            'text': bleach.clean(data['text']),
            'id': int(tweet.tweet_id),
            'date': date,
        })
    return tweets

def more_tweets(request):
    return jingo.render(request, 'customercare/tweets.html', 
                        { 'tweets': _get_tweets() })

@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    twitter = request.twitter

    canned_responses = CannedCategory.objects.all()

    resp = jingo.render(request, 'customercare/landing.html', {
        'canned_responses': canned_responses,
        'tweets': _get_tweets(),
        'authed': twitter.authed,
    })

    return resp

def is_printable(s, codec='utf-8'):
    try: s.decode(codec)
    except UnicodeDecodeError: return False
    else: return True

@twitter.auth_required
def twitter_post(request):
    reply_to = int(request.POST.get('reply_to'))
    reply_to_name = request.POST.get('reply_to_name')
    content = request.POST.get('content')

    generic_error = 'Sorry, an error occurred'

    if not is_printable(content):
        return http.HttpResponseBadRequest('{0} ({1})'.format(generic_error, 
                                                              'content is not printable'))
    elif len(content) == 0:
        return http.HttpResponseBadRequest('Message is empty')
    elif len(content) > 140:
        return http.HttpResponseBadRequest('Message is too long')
    else:
        try:
            request.twitter.api.update_status(content, reply_to)
        except tweepy.TweepError, e:
            return http.HttpResponseBadRequest('{0} ({1})'.format(generic_error, e))
        else:
            return http.HttpResponse()
