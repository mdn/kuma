from django.contrib.auth import logout
from django.shortcuts import render
from django.utils.cache import add_never_cache_headers

from .models import UserBan


class BanMiddleware(object):
    """
    Middleware implementing bans. HTTP requests from banned users will
    be logged out, and shown a message explaining that they are
    banned.
    """
    def process_request(self, request):
        # Checking request.user.is_authenticated() will access the session,
        # and the SessionMiddleware will add Vary: Cookie. Avoid it by
        # checking, then resetting request.session.accessed to the previous
        # value (hopefully False).
        old_session_accessed = request.session.accessed
        is_auth = hasattr(request, 'user') and request.user.is_authenticated()
        request.session.accessed = old_session_accessed

        if is_auth:
            bans = UserBan.objects.filter(user=request.user,
                                          is_active=True)
            if not bans:
                return None
            logout(request)
            banned_response = render(request, 'users/user_banned.html', {
                'bans': bans,
                'path': request.path
            })
            add_never_cache_headers(banned_response)
            return banned_response
        return None
