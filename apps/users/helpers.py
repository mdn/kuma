from django.conf import settings

import jinja2
from jingo import register

from users.models import Profile


@register.function
def profile_url(user):
    """Return a URL to the user's profile."""
    # TODO: revisit this when we have a users app
    return '/tiki-user_information.php?locale=en-US&userId=%s' % user.id


@register.function
def profile_avatar(user):
    """Return a URL to the user's avatar."""
    try:  # This is mostly for tests.
        profile = user.get_profile()
    except Profile.DoesNotExist:
        return settings.DEFAULT_AVATAR
    return profile.avatar.url if profile.avatar else settings.DEFAULT_AVATAR


@register.filter
def public_email(email):
    """Email address -> publicly displayable email."""
    return jinja2.Markup(email.replace(u'@', u' [at] '))
