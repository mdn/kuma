import pytest
from django.conf import settings

from ..templatetags.jinja_helpers import (get_avatar_url, is_username_taken,
                                          public_email)


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


@pytest.mark.parametrize('case', ('upper', 'lower'))
def test_is_username_taken_existing_user(wiki_user, case):
    """
    Test is_username_taken for an existing user, and also that the username is
    case insensitive.
    """
    assert is_username_taken(getattr(str, case)(wiki_user.username))


@pytest.mark.parametrize('username', ('nonexistent', None))
def test_is_username_taken_nonexisting_user(wiki_user, username):
    """Test is_username_taken for an non-existing user."""
    assert not is_username_taken(username)
