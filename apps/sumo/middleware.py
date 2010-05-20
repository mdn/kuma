"""
Taken from zamboni.amo.middleware.

Tried to use localeurl but it choked on 'en-US' with capital letters.
"""

import urllib

from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_str
from django.contrib import auth

import tower

from . import urlresolvers
from .models import Session
from sumo.helpers import urlparams


class LocaleURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = urlresolvers.Prefixer(request)
        urlresolvers.set_url_prefix(prefixer)
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
            new_locale, _ = prefixer.split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        tower.activate(prefixer.locale)


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
