import hashlib
import urllib

from django.conf import settings

from kuma.core.jobs import KumaJob


class UserGravatarURLJob(KumaJob):
    """
    Produce a gravatar image URL from email address.
    """
    lifetime = 60 * 60 * 24

    def fetch(self, email, secure=True, size=220, rating='pg',
              default=settings.DEFAULT_AVATAR):
        base_url = (secure and 'https://secure.gravatar.com' or
                    'http://www.gravatar.com')
        email_hash = hashlib.md5(email.lower().encode('utf8'))
        params = urllib.urlencode({'s': size, 'd': default, 'r': rating})
        return '%(base_url)s/avatar/%(hash)s?%(params)s' % {
            'base_url': base_url,
            'hash': email_hash.hexdigest(),
            'params': params,
        }
