import logging
from uuid import uuid4

from django import http
from django.core.cache import cache

import tweepy


log = logging.getLogger('k')

PREFIX = 'custcare_'
ACCESS_NAME = PREFIX + 'access'
REDIRECT_NAME = PREFIX + 'redirect'
REQUEST_KEY_NAME = PREFIX + 'request_key'
REQUEST_SECRET_NAME = PREFIX + 'request_secret'

MAX_AGE = 3600


def url(request, override=None):
    d = {
        'scheme': 'https' if request.is_secure() else 'http',
        'host': request.get_host(),
        'path': request.get_full_path(),
    }
    if override:
        d.update(override)
    
    return '{0}://{1}{2}'.format(d['scheme'], d['host'], d['path'])

# Twitter sessions are SSL only, so redirect to SSL if needed
def auth_wanted(view_func):
    def wrapper(request, *args, **kwargs):

        if request.COOKIES.get(REDIRECT_NAME) and not request.is_secure():
            ssl_url = url(request, {'scheme': 'https'})
            return http.HttpResponseRedirect(ssl_url)

        return view_func(request, *args, **kwargs)
    return wrapper

# returns a HttpResponseBadRequest in not authed
def auth_required(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.twitter.authed:
            return http.HttpResponseBadRequest()

        return view_func(request, *args, **kwargs)
    return wrapper


class Session(object):
    id = None
    key = None
    secret = None

    @property
    def cachekey_key(self):
        return '{0}_key_{1}'.format(ACCESS_NAME, self.id)

    @property
    def cachekey_secret(self):
        return '{0}_secret_{1}'.format(ACCESS_NAME, self.id)

    @property
    def authed(self):
        return bool(self.id and self.key and self.secret)

    def __init__(self, key=None, secret=None):
        self.id = uuid4().hex
        self.key = key
        self.secret = secret

    @classmethod
    def from_request(cls, request):
        s = cls()
        s.id = request.COOKIES.get(ACCESS_NAME)
        s.key = cache.get(s.cachekey_key)
        s.secret = cache.get(s.cachekey_secret)
        return s

    def delete(self, response):
        response.delete_cookie(REDIRECT_NAME)
        response.delete_cookie(ACCESS_NAME)
        cache.delete(self.cachekey_key)
        cache.delete(self.cachekey_secret)
        self.id = None
        self.key = None
        self.secret = None

    def save(self, response):
        cache.set(self.cachekey_key, self.key, MAX_AGE)
        cache.set(self.cachekey_secret, self.secret, MAX_AGE)
        response.set_cookie(REDIRECT_NAME, '1', max_age=MAX_AGE)
        response.set_cookie(ACCESS_NAME, self.id, max_age=MAX_AGE, secure=True)


