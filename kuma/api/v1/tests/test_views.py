import pytest

from django.contrib.auth.models import User

from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse


@pytest.mark.parametrize("http_method", ["put", "post", "delete", "options", "head"])
def test_whoami_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse("api.v1.whoami")
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_anonymous(client):
    """Test response for anonymous users."""
    url = reverse("api.v1.whoami")
    response = client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json() == {}
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_anonymous_cloudfront_geo(client):
    """Test response for anonymous users."""
    url = reverse("api.v1.whoami")
    response = client.get(url, HTTP_CLOUDFRONT_VIEWER_COUNTRY_NAME="US of A")
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json()["geo"] == {"country": "US of A"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_staff,is_superuser",
    [(False, False), (True, True)],
    ids=("muggle", "wizard"),
)
def test_whoami(
    user_client,
    wiki_user,
    is_staff,
    is_superuser,
):
    """Test responses for logged-in users."""
    wiki_user.is_staff = is_staff
    wiki_user.is_superuser = is_superuser
    wiki_user.is_staff = is_staff
    wiki_user.save()
    url = reverse("api.v1.whoami")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    expect = {
        "username": wiki_user.username,
        "is_authenticated": True,
        "avatar_url": None,  # temporary
        # "subscriber_number": None,
        "email": "wiki_user@example.com",
    }
    if is_staff:
        expect["is_staff"] = True
    if is_superuser:
        expect["is_superuser"] = True

    assert response.json() == expect
    assert_no_cache_header(response)


# @pytest.mark.django_db
# def test_whoami_subscriber(
#     user_client,
#     wiki_user,
# ):
#     """Test responses for logged-in users and whether they have an active
#     subscription."""
#     url = reverse("api.v1.whoami")
#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert "is_subscriber" not in response.json()

#     UserSubscription.set_active(wiki_user, "abc123")
#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert response.json()["is_subscriber"] is True
#     assert response.json()["subscriber_number"] == 1

#     UserSubscription.set_canceled(wiki_user, "abc123")
#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert "is_subscriber" not in response.json()
#     assert response.json()["subscriber_number"] == 1


@pytest.mark.django_db
def test_account_settings_auth(client):
    url = reverse("api.v1.settings")
    response = client.get(url)
    assert response.status_code == 403
    response = client.delete(url)
    assert response.status_code == 403
    response = client.post(url, {})
    assert response.status_code == 403


def test_account_settings_delete(user_client, wiki_user):
    username = wiki_user.username
    response = user_client.delete(reverse("api.v1.settings"))
    assert response.status_code == 200
    assert not User.objects.filter(username=username).exists()


# def test_get_and_set_settings_happy_path(user_client):
#     url = reverse("api.v1.settings")
#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert_no_cache_header(response)
#     assert response.json()["locale"] == "en-US"

#     response = user_client.post(url, {"locale": "zh-CN"})
#     assert response.status_code == 200

#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert response.json()["locale"] == "zh-CN"

#     # You can also omit certain things and things won't be set
#     response = user_client.post(url, {})
#     assert response.status_code == 200
#     response = user_client.get(url)
#     assert response.status_code == 200
#     assert response.json()["locale"] == "zh-CN"


# def test_set_settings_validation_errors(user_client):
#     url = reverse("api.v1.settings")
#     response = user_client.post(url, {"locale": "never heard of"})
#     assert response.status_code == 400
#     assert response.json()["errors"]["locale"][0]["code"] == "invalid_choice"
#     assert response.json()["errors"]["locale"][0]["message"]
