from datetime import datetime
from email.Utils import parsedate
import json
import logging
from uuid import uuid4

from django import http
from django.conf import settings
from django.core.cache import cache

import jingo
import tweepy

from .models import CannedCategory, Tweet


log = logging.getLogger('custcare')

token_cache_prefix = 'custcare_token_'
key_prefix = token_cache_prefix + 'key_'
secret_prefix = token_cache_prefix + 'secret_'

# cookie names are duplicated in js/cusomtercare.js
access_cookie_name = 'custcare_twitter_access_id'
redirect_cookie_name = 'custcare_twitter_redirect_flag'


def auth_factory(request):
    return tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, 
                               settings.TWITTER_CONSUMER_SECRET,
                               'https://{0}/{1}/customercare/'.format(
                                   request.get_host(), request.locale))


def set_access_cookie(resp, id):
    resp.set_cookie(redirect_cookie_name, '1', httponly=True)
    resp.set_cookie(access_cookie_name, id, secure=True)


def set_tokens(id, key, secret):
    cache.set(key_prefix + id, key)
    cache.set(secret_prefix + id, secret)


def get_tokens(id):
    key = cache.get(key_prefix + id)
    secret = cache.get(secret_prefix + id)
    return key, secret


def landing(request):
    """Customer Care Landing page."""

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
            'date': date,
        })

    resp = jingo.render(request, 'customercare/landing.html', {
        'canned_responses': canned_responses,
        'tweets': tweets,
        'now': datetime.utcnow(),
    })

    # TODO HTTP redirect flag checking?
    if request.COOKIES.get(redirect_cookie_name):
        return http.HttpResponseRedirect('https://{0}/{1}'.format(
            request.get_host(), request.get_full_path()))

    # if GET[oauth_verifier] exists, we're handling an OAuth login
    verifier = request.GET.get('oauth_verifier')
    if verifier:
        auth = auth_factory(request)
        request_key = request.COOKIES.get('request_token_key')
        request_secret = request.COOKIES.get('request_token_secret')
        if request_key and request_secret:
            resp.delete_cookie('request_token_key')
            resp.delete_cookie('request_token_secret')
            auth.set_request_token(request_key, request_secret)

            try:
                auth.get_access_token(verifier)
            except tweepy.TweepError:
                log.warning('Tweepy Error with verifier token')
                pass
            else:
                access_id = uuid4().hex
                set_access_cookie(resp, access_id)
                set_tokens(access_id, auth.access_token.key, auth.access_token.secret)

    return resp


def twitter_post(request):
    #    access_id = request.COOKIES.get(access_cookie_name)
    #    if access_id:
    #        key, secret = get_tokens(access_id)
    #        authed = True
    #        resp.write('key: %s  sec: %s' % (key, secret))
    #        set_access_cookie(resp, access_id)
    pass


def twitter_auth(request):
    auth = auth_factory(request)

    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError:
        log.warning('Tweepy error while getting authorization url')
        return http.HttpReponseServerError()

    resp = http.HttpResponseRedirect(redirect_url)
    resp.set_cookie('request_token_key', auth.request_token.key, max_age=3600, secure=True)
    resp.set_cookie('request_token_secret', auth.request_token.secret, max_age=3600, secure=True)
    return resp
