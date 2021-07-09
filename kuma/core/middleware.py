from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.urls import get_script_prefix, is_valid_path
from waffle.middleware import WaffleMiddleware

from .decorators import add_shared_cache_control
from .i18n import (
    activate_language_from_request,
    get_language,
    get_language_from_path,
)


class MiddlewareBase(object):
    def __init__(self, get_response):
        self.get_response = get_response


class SetRemoteAddrFromForwardedFor(MiddlewareBase):
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set. This is useful if you're sitting behind a reverse proxy that
    causes each request's REMOTE_ADDR to be set to 127.0.0.1.
    """

    def __call__(self, request):
        try:
            forwarded_for = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            pass
        else:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # The client's IP will be the first one.
            forwarded_for = forwarded_for.split(",")[0].strip()
            request.META["REMOTE_ADDR"] = forwarded_for

        return self.get_response(request)


class ForceAnonymousSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        """
        Always create an anonymous session.
        """
        request.session = self.SessionStore(None)

    def process_response(self, request, response):
        """
        Override the base-class method to ensure we do nothing.
        """
        return response


class WaffleWithCookieDomainMiddleware(WaffleMiddleware):
    """
    The waffle.middleware.WaffleMiddleware class does not yet provide a way
    way to configure the domain of the cookies it adds to the response. This
    class is a simple wrapper around the waffle.middleware.WaffleMiddleware
    class, and it simply sets the domain of all cookies added to the response
    by waffle.middleware.WaffleMiddleware. The domain is set to the value
    configured in settings.WAFFLE_COOKIE_DOMAIN.
    """

    def process_response(self, request, response):
        keys_before = frozenset(response.cookies.keys())
        try:
            response = super(WaffleWithCookieDomainMiddleware, self).process_response(
                request, response
            )
        finally:
            keys_after = frozenset(response.cookies.keys())
            for key in keys_after - keys_before:
                response.cookies[key]["domain"] = settings.WAFFLE_COOKIE_DOMAIN
        return response
