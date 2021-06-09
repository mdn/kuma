import pytest
from allauth.socialaccount.models import SocialAccount
from django.conf import settings

from ..templatetags.jinja_helpers import get_avatar_url, is_username_taken


@pytest.mark.parametrize(
    "providers",
    (
        ("persona",),
        ("persona", "github", "google"),
        ("persona", "google", "github"),
    ),
    ids=("default", "github", "google"),
)
def test_get_avatar_url(wiki_user, providers):
    SOCIAL_ACCOUNT_DATA = {
        "github": {
            "uid": 1234567,
            "extra_data": {"avatar_url": "https://github/yada/yada"},
        },
        "google": {
            "uid": 123456789012345678901,
            "extra_data": {"picture": "https://google/yada/yada"},
        },
        "persona": {"uid": wiki_user.email},
    }
    first_valid_avatar_url = None
    for provider in providers:
        sa = SocialAccount.objects.create(
            user=wiki_user, provider=provider, **SOCIAL_ACCOUNT_DATA[provider]
        )
        if (not first_valid_avatar_url) and (provider != "persona"):
            first_valid_avatar_url = sa.get_avatar_url()
    assert get_avatar_url(wiki_user) == (
        first_valid_avatar_url or settings.DEFAULT_AVATAR
    )


def test_get_avatar_url_default(wiki_user):
    assert get_avatar_url(wiki_user) == settings.DEFAULT_AVATAR


def test_is_username_taken(wiki_user):
    assert is_username_taken(wiki_user.username)
    assert is_username_taken(wiki_user.username.upper())
    assert not is_username_taken("nonexistent")
    assert not is_username_taken(None)
