from datetime import datetime
from email.Utils import parsedate
import json
import logging

from django import http
from django.views.decorators.csrf import csrf_exempt

import jingo

from .models import CannedCategory, Tweet
import twitter

log = logging.getLogger('k')


@twitter.auth_wanted
def landing(request):
    """Customer Care Landing page."""

    twitter = request.twitter

    canned_responses = CannedCategory.objects.all()
    tweets = []
    for tweet in Tweet.objects.filter(locale='en')[:10]:
        data = json.loads(tweet.raw_json)
        parsed_date = parsedate(data['created_at'])
        date = datetime(*parsed_date[0:6])
        tweets.append({
            'profile_img': data['profile_image_url'],
            'user': data['from_user'],
            'text': tweet,
            'reply_to': tweet.tweet_id,
            'date': date,
        })

    resp = jingo.render(request, 'customercare/landing.html', {
        'canned_responses': canned_responses,
        'tweets': tweets,
        'authed': twitter.authed,
    })

    return resp


@csrf_exempt
@twitter.auth_required
def twitter_post(request):
    # FIXME ensure post length is under twitter limit
    # do this in JS too
    tweet = request.POST.get('tweet')
    reply_to = request.POST.get('reply_to')
    # TODO remove debug line
    request.twitter.api.update_status(tweet, '25684040574')
    return http.HttpResponse()
