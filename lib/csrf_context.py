from django.core import context_processors
from django.utils import functional, html


def csrf(request):
    # Use lazy() because getting the token triggers Set-Cookie: csrftoken.
    def _get_val():
        token = context_processors.csrf(request)['csrf_token']
        # This should be an md5 string so any broken Unicode is an attacker.
        try:
            return html.escape(unicode(token))
        except UnicodeDecodeError:
            return u''
    return {'csrf_token': functional.lazy(_get_val, unicode)()}
