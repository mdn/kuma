import logging

from django import http
from django.conf import settings

from . import *
import tweepy


log = logging.getLogger('k')


class SessionMiddleware(object):

    def process_request(self, request):
        if getattr(request, 'twitter', False):
            return

        request.twitter = Session.from_request(request)

        auth = tweepy.OAuthHandler(settings.TWITTER_CONSUMER_KEY, 
                                   settings.TWITTER_CONSUMER_SECRET,
                                   ssl_url(request),
                                   secure=True)

        if request.GET.get('twitter_delete_auth'):
            request.twitter = Session.factory()

        elif request.twitter.authed:
            auth.set_access_token(request.twitter.key, request.twitter.secret)
            request.twitter.api = tweepy.API(auth)

        else:
        
            verifier = request.GET.get('oauth_verifier')
            if verifier:
                # We are completing an OAuth login

                request_key = request.COOKIES.get(REQUEST_KEY_NAME)
                request_secret = request.COOKIES.get(REQUEST_SECRET_NAME)

                if request_key and request_secret:
                    auth.set_request_token(request_key, request_secret)

                    try:
                        auth.get_access_token(verifier)
                    except tweepy.TweepError:
                        log.warning('Tweepy Error with verifier token')
                        pass
                    else:
                        request.twitter = Session.factory(
                            auth.access_token.key, auth.access_token.secret)

            elif request.GET.get('twitter_auth_request'):
                # We are requesting Twitter auth

                try:
                    redirect_url = auth.get_authorization_url()
                except tweepy.TweepError:
                    log.warning('Tweepy error while getting authorization url')
                else:
                    response = http.HttpResponseRedirect(redirect_url)
                    response.set_cookie(REQUEST_KEY_NAME, auth.request_token.key, 
                                        max_age=MAX_AGE, secure=True)
                    response.set_cookie(REQUEST_SECRET_NAME, auth.request_token.secret, 
                                        max_age=MAX_AGE, secure=True)
                    return response


    def process_response(self, request, response):
        if getattr(request, 'twitter', False):
            if request.GET.get('twitter_delete_auth'):
                request.twitter.delete(response)

            if request.twitter.authed:
                response.delete_cookie(REQUEST_KEY_NAME)
                response.delete_cookie(REQUEST_SECRET_NAME)
                request.twitter.save(response)

        return response
