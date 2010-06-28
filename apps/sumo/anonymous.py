"""
Django middleware for identifying unauthenticated users using a cookie.
This is used in kitsune to keep track of their actions such as voting and
submitting questions.

The middleware adds an `anonymous` attribute to the request object. It is
initialized to the value of the anonymous id cookie, if set.

The anonymous id will be generated automatically when
`request.anonymous.attribute_id` is first accessed. In order to check if
it is set without generating one, use `request.anonymous.has_id`. Once the
anonymous id is generated, it will be set in a cookie in the response.


Required Settings:

ANONYMOUS_COOKIE_NAME
Name of the cookie to use

ANONYMOUS_COOKIE_MAX_AGE
Maximum age of the cookie, in seconds.
"""


import time
import os
import random
# Use the system (hardware-based) random number generator if it exists.
if hasattr(random, 'SystemRandom'):
    randrange = random.SystemRandom().randrange
else:
    randrange = random.randrange

from django.conf import settings
from django.utils.http import cookie_date
from django.utils.hashcompat import md5_constructor


MAX_ANONYMOUS_ID = 18446744073709551616L     # 2 << 63


class AnonymousIdentity(object):
    """Used to generate an id for anonymous users."""
    def __init__(self, anonymous_id=None):
        self._anonymous_id = anonymous_id
        self.modified = False

    @property
    def has_id(self):
        return self._anonymous_id != None

    @property
    def anonymous_id(self):
        if not self._anonymous_id:
            self._anonymous_id = self._generate_id()
            self.modified = True

        return self._anonymous_id

    def _generate_id(self):
        # This code is mostly borrowed from SessionBase._get_new_session_key()

        # The random module is seeded when this Apache child is created.
        # Use settings.SECRET_KEY as added salt.
        try:
            pid = os.getpid()
        except AttributeError:
            # No getpid() in Jython, for example
            pid = 1

        anon_id = md5_constructor("%s%s%s%s"
                                  % (randrange(0, MAX_ANONYMOUS_ID),
                                     pid, time.time(),
                                     settings.SECRET_KEY)).hexdigest()
        return anon_id


class AnonymousIdentityMiddleware(object):
    """Middleware for identifying anonymous users via a cookie."""
    def process_request(self, request):
        anonymous_id = request.COOKIES.get(settings.ANONYMOUS_COOKIE_NAME,
                                           None)
        request.anonymous = AnonymousIdentity(anonymous_id)

    def process_response(self, request, response):
        """If request.anonymous was modified set the anonymous cookie."""
        try:
            modified = request.anonymous.modified
        except AttributeError:
            pass
        else:
            if modified:
                max_age = settings.ANONYMOUS_COOKIE_MAX_AGE
                expires_time = time.time() + max_age
                expires = cookie_date(expires_time)
                response.set_cookie(settings.ANONYMOUS_COOKIE_NAME,
                                    request.anonymous.anonymous_id,
                                    max_age=max_age,
                                    expires=expires)

        return response
