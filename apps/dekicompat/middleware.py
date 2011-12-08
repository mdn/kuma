from django.core.exceptions import ImproperlyConfigured

from django.contrib import auth

import commonware

log = commonware.log.getLogger('kuma.dekicompat')

class DekiUserMiddleware(object):
    """
    This middleware is to be used in conjunction with the 
    ``DekiUserBackend`` to authenticate via Dekiwiki.
    """
    def process_request(self, request):
        """
        TODO This is a good check and was working until I went to commit...

        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Dekicombat auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the DekiUserMiddleware class.")
        """
        try:
            auth_token = request.COOKIES['authtoken']
        except KeyError:
            # If specified header doesn't exist then return (leaving
            # request.user set to AnonymousUser by the
            # AuthenticationMiddleware).
            return
        # TODO(aok) Session or other cache?
        if not auth_token:
            return

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(authtoken=auth_token)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)
