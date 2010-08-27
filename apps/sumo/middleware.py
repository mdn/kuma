"""
Taken from zamboni.amo.middleware.

Tried to use localeurl but it choked on 'en-US' with capital letters.
"""

import urllib

from django.http import HttpResponsePermanentRedirect, HttpResponseForbidden
from django.utils.encoding import smart_str
from django.contrib import auth

import tower

from .urlresolvers import Prefixer, set_url_prefixer, split_path
from .models import Session
from sumo.helpers import urlparams
from sumo.views import handle403


class LocaleURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = Prefixer(request)
        set_url_prefixer(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if 'lang' in request.GET:
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.
            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), request.GET[k]) for k in request.GET)
            query.pop('lang')
            return HttpResponsePermanentRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        tower.activate(prefixer.locale)

    def process_response(self, request, response):
        """Unset the thread-local var we set during `process_request`."""
        # This makes mistaken tests (that should use LocalizingClient but
        # use Client instead) fail loudly and reliably. Otherwise, the set
        # prefixer bleeds from one test to the next, making tests
        # order-dependent and causing hard-to-track failures.
        set_url_prefixer(None)
        return response


class TikiCookieMiddleware(object):
    """
    This middleware looks at the SUMOv1 cookie set by Tiki and authenticates
    the user in django.
    """

    def process_request(self, request):
        """Look up the SUMOv1 cookie and authenticate the user"""

        id = request.COOKIES.get('SUMOv1')

        if id:
            try:
                session = Session.objects.get(pk=id)
            except Session.DoesNotExist:
                return
            user = auth.authenticate(session=session)
            if user is not None:
                auth.login(request, user)


class Forbidden403Middleware(object):
    """
    Renders a 403.html page if response.status_code == 403.
    """
    def process_response(self, request, response):
        if isinstance(response, HttpResponseForbidden):
            return handle403(request)
        # If not 403, return response unmodified
        return response


class NoCacheHttpsMiddleware(object):
    """
    Sets no-cache headers when HTTPS META variable is set
    and not equal to 'off'.
    """
    def process_response(self, request, response):
        if 'HTTPS' in request.META and request.META['HTTPS'] != 'off':
            response['Expires'] = 'Thu, 19 Nov 1981 08:52:00 GMT'
            response['Cache-Control'] = 'no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'
        return response
