from django.conf import settings
from django.contrib import admin
from django.utils.translation import gettext
from django_jinja import library
from jinja2 import Markup

from kuma.core.urlresolvers import reverse

from ..models import User


@library.global_function
def get_avatar_url(user):
    """
    Get the avatar URL of the user's first-joined social account that has one,
    excluding all Persona social accounts. Assumes that the user is not None or
    anonymous. If the user has no social account with an avatar, returns the
    default avatar URL.
    """
    for account in user.socialaccount_set.exclude(provider="persona").order_by(
        "date_joined"
    ):
        avatar_url = account.get_avatar_url()
        if avatar_url:
            return avatar_url
    return settings.DEFAULT_AVATAR


@library.global_function
def admin_link(user):
    """Returns a link to admin a user"""
    url = reverse(
        "admin:users_user_change", args=(user.id,), current_app=admin.site.name
    )
    link = (
        '<a href="%s" class="button neutral">%s'
        '<i aria-hidden="true" class="icon-wrench"></i></a>' % (url, gettext("Admin"))
    )
    return Markup(link)


@library.global_function
def is_username_taken(username):
    """
    Returns True if a user with the given username exists (case-insentive),
    otherwise False.
    """
    return User.objects.filter(username=username).exists()
