import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from ..templatetags.jinja_helpers import get_avatar_url, public_email


@pytest.mark.parametrize(
    'user', (None, AnonymousUser()), ids=('none', 'anonymous'))
def test_get_avatar_url_no_user(user):
    assert get_avatar_url(user) is None


def test_get_avatar_url(wiki_user, wiki_user_github_account):
    assert (get_avatar_url(wiki_user) ==
            wiki_user_github_account.get_avatar_url())


def test_get_avatar_url_default(wiki_user):
    assert get_avatar_url(wiki_user) == settings.DEFAULT_AVATAR


def test_public_email():
    assert ('<span class="email">'
            '&#109;&#101;&#64;&#100;&#111;&#109;&#97;&#105;&#110;&#46;&#99;'
            '&#111;&#109;</span>' == public_email('me@domain.com'))
    assert ('<span class="email">'
            '&#110;&#111;&#116;&#46;&#97;&#110;&#46;&#101;&#109;&#97;&#105;'
            '&#108;</span>' == public_email('not.an.email'))
