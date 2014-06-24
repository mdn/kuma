import urllib
import hashlib

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from jinja2 import escape, Markup
from jingo import register

from tower import ugettext as _

from sumo.urlresolvers import reverse

DEFAULT_AVATAR = getattr(settings, 'DEFAULT_AVATAR',
                         settings.MEDIA_URL + 'img/avatar-default.png')


@register.function
def gravatar_url(user, secure=True, size=220, rating='pg',
                 default=DEFAULT_AVATAR):
    """Produce a gravatar image URL from email address."""
    base_url = (secure and 'https://secure.gravatar.com' or
                'http://www.gravatar.com')
    email_hash = hashlib.md5(user.email.lower().encode('utf8'))
    params = urllib.urlencode({'s': size, 'd': default, 'r': rating})
    return '%(base_url)s/avatar/%(hash)s?%(params)s' % {
        'base_url': base_url,
        'hash': email_hash.hexdigest(),
        'params': params,
    }


@register.function
def display_name(user):
    """Return a display name if set, else the username."""
    try:  # Also mostly for tests.
        profile = user.get_profile()
    except ObjectDoesNotExist:
        return user.username
    return profile.fullname if profile.fullname else user.username


@register.function
def ban_link(ban_user, banner_user):
    """Returns a link to ban a user"""
    link = ''
    if ban_user.id != banner_user.id and banner_user.has_perm('users.add_userban'):
        url = '%s?user=%s&by=%s' % (reverse('admin:users_userban_add'), ban_user.id, banner_user.id)
        link = '<a href="%s" class="button ban-link">%s</a>' % (url, _('Ban User'))
    return Markup(link)


@register.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return Markup('<span class="email">%s</span>' % unicode_to_html(email))


def unicode_to_html(text):
    """Turns all unicode into html entities, e.g. &#69; -> E."""
    return ''.join([u'&#%s;' % ord(i) for i in text])


@register.function
def user_list(users):
    """Turn a list of users into a list of links to their profiles."""
    link = u'<a href="%s">%s</a>'
    list = u', '.join([link % (escape(u.get_absolute_url()), escape(u.username)) for
                       u in users])
    return Markup(list)
