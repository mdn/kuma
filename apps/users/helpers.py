from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from jinja2 import escape, Markup
from jingo import register

from sumo.urlresolvers import reverse


@register.function
def profile_url(user):
    """Return a URL to the user's profile."""
    return reverse('devmo_profile_view', args=[user.username])


@register.function
def profile_avatar(user):
    """Return a URL to the user's avatar."""
    try:  # This is mostly for tests.
        profile = user.get_profile()
    except ObjectDoesNotExist:
        return settings.DEFAULT_AVATAR
    return profile.gravatar if profile.gravatar else settings.DEFAULT_AVATAR


@register.function
def display_name(user):
    """Return a display name if set, else the username."""
    try:  # Also mostly for tests.
        profile = user.get_profile()
    except ObjectDoesNotExist:
        return user.username
    return profile.fullname if profile.fullname else user.username


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
    list = u', '.join([link % (escape(profile_url(u)), escape(u.username)) for
                       u in users])
    return Markup(list)
