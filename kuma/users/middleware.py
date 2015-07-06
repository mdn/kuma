from django.contrib.auth import logout
from django.shortcuts import render

from .models import UserBan


class BanMiddleware(object):
    """
    Middleware implementing bans. HTTP requests from banned users will
    be logged out, and shown a message explaining that they are
    banned.
    """
    def process_request(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated():
            bans = UserBan.objects.filter(user=request.user,
                                          is_active=True)
            if not bans:
                return None
            logout(request)
            return render(request,
                          'users/user_banned.html',
                          {'bans': bans,
                           'path': request.path})
        return None
