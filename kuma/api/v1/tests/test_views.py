from unittest.mock import patch

import pytest

from django.conf import settings
from waffle.models import Flag, Sample, Switch
from waffle.testutils import override_flag

from kuma.api.v1.views import document_api_data, get_content_based_redirect, get_s3_key
from kuma.core.ga_tracking import (
    ACTION_SUBSCRIPTION_FEEDBACK,
    CATEGORY_MONTHLY_PAYMENTS,
)
from kuma.core.tests import assert_no_cache_header
from kuma.core.urlresolvers import reverse
from kuma.search.tests import ElasticTestCase
from kuma.users.models import UserSubscription
from kuma.wiki.models import BCSignal
from kuma.wiki.templatetags.jinja_helpers import absolutify


def test_get_s3_key(root_doc):
    locale, slug = root_doc.locale, root_doc.slug
    expected_key = "api/v1/doc/{}/{}.json".format(locale, slug)
    assert get_s3_key(root_doc) == get_s3_key(locale=locale, slug=slug) == expected_key
    assert (
        get_s3_key(root_doc, prefix_with_forward_slash=True)
        == get_s3_key(locale=locale, slug=slug, prefix_with_forward_slash=True)
        == "/" + expected_key
    )


@pytest.mark.parametrize(
    "case",
    ("normal", "redirect", "redirect-to-self", "redirect-to-home", "redirect-to-wiki"),
)
def test_get_content_based_redirect(
    root_doc, redirect_doc, redirect_to_self, redirect_to_home, redirect_to_macros, case
):
    if case == "normal":
        doc = root_doc
        expected = None
    elif case == "redirect":
        doc = redirect_doc
        expected = (
            get_s3_key(
                root_doc, prefix_with_forward_slash=True, suffix_file_extension=False
            ),
            True,
        )
    elif case == "redirect-to-self":
        doc = redirect_to_self
        expected = None
    elif case == "redirect-to-home":
        doc = redirect_to_home
        expected = ("/en-US/", False)
    else:
        doc = redirect_to_macros
        expected = (absolutify("/en-US/dashboards/macros", for_wiki_site=True), False)
    assert get_content_based_redirect(doc) == expected


@pytest.mark.parametrize("http_method", ["put", "post", "delete", "options", "head"])
def test_doc_api_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse("api.v1.doc", args=["en-US", "Web/CSS"])
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_doc_api_404(client, root_doc):
    """We get a 404 if we ask for a document that does not exist."""
    url = reverse("api.v1.doc", args=["en-US", "NoSuchPage"])
    response = client.get(url)
    assert response.status_code == 404
    assert_no_cache_header(response)


def test_doc_api(client, trans_doc):
    """On success we get document details in a JSON response."""
    url = reverse("api.v1.doc", args=[trans_doc.locale, trans_doc.slug])
    response = client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data["documentData"]
    assert data["redirectURL"] is None
    doc_data = data["documentData"]
    assert doc_data["locale"] == trans_doc.locale
    assert doc_data["slug"] == trans_doc.slug
    assert doc_data["id"] == trans_doc.id
    assert doc_data["title"] == trans_doc.title
    assert doc_data["language"] == trans_doc.language
    assert doc_data["hrefLang"] == "fr"
    assert doc_data["absoluteURL"] == trans_doc.get_absolute_url()
    assert doc_data["wikiURL"] == absolutify(
        trans_doc.get_absolute_url(), for_wiki_site=True
    )
    assert doc_data["editURL"] == absolutify(
        reverse("wiki.edit", args=(trans_doc.slug,), locale=trans_doc.locale),
        for_wiki_site=True,
    )
    assert doc_data["translateURL"] is None
    assert doc_data["bodyHTML"] == trans_doc.get_body_html()
    assert doc_data["quickLinksHTML"] == trans_doc.get_quick_links_html()
    assert doc_data["tocHTML"] == trans_doc.get_toc_html()
    assert doc_data["translations"] == [
        {
            "locale": "en-US",
            "language": "English (US)",
            "hrefLang": "en",
            "localizedLanguage": "Anglais am\u00e9ricain",
            "title": "Root Document",
            "url": "/en-US/docs/Root",
        }
    ]
    assert doc_data["lastModified"] == "2017-04-14T12:20:00"


def test_doc_api_for_redirect_to_doc(client, root_doc, redirect_doc):
    """
    Test the document API when we're requesting data for a document that
    redirects to another document.
    """
    url = reverse("api.v1.doc", args=[redirect_doc.locale, redirect_doc.slug])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data["documentData"]
    assert data["redirectURL"] is None
    doc_data = data["documentData"]
    assert doc_data["locale"] == root_doc.locale
    assert doc_data["slug"] == root_doc.slug
    assert doc_data["id"] == root_doc.id
    assert doc_data["title"] == root_doc.title
    assert doc_data["language"] == root_doc.language
    assert doc_data["hrefLang"] == "en"
    assert doc_data["absoluteURL"] == root_doc.get_absolute_url()
    assert doc_data["wikiURL"] == absolutify(
        root_doc.get_absolute_url(), for_wiki_site=True
    )
    assert doc_data["translateURL"] == absolutify(
        reverse("wiki.select_locale", args=(root_doc.slug,), locale=root_doc.locale,),
        for_wiki_site=True,
    )
    assert doc_data["bodyHTML"] == root_doc.get_body_html()
    assert doc_data["quickLinksHTML"] == root_doc.get_quick_links_html()
    assert doc_data["tocHTML"] == root_doc.get_toc_html()
    assert doc_data["translations"] == []
    assert doc_data["lastModified"] == "2017-04-14T12:15:00"


@pytest.mark.parametrize("case", ("redirect-to-home", "redirect-to-other"))
def test_doc_api_for_redirect_to_non_doc(
    client, redirect_to_home, redirect_to_macros, case
):
    """
    Test the document API when we're requesting data for a document that
    redirects to a non-document page (either the home page or another).
    """
    if case == "redirect-to-home":
        doc = redirect_to_home
        expected_redirect_url = "/en-US/"
    else:
        doc = redirect_to_macros
        expected_redirect_url = absolutify(
            "/en-US/dashboards/macros", for_wiki_site=True
        )
    url = reverse("api.v1.doc", args=[doc.locale, doc.slug])
    response = client.get(url)
    assert response.status_code == 200
    assert_no_cache_header(response)

    data = response.json()
    assert data["documentData"] is None
    assert data["redirectURL"] == expected_redirect_url

    # Also ensure that we get exactly the same data by calling
    # the document_api_data() function directly
    assert data == document_api_data(redirect_url=expected_redirect_url)


@pytest.mark.parametrize("http_method", ["put", "post", "delete", "options", "head"])
def test_whoami_disallowed_methods(client, http_method):
    """HTTP methods other than GET are not allowed."""
    url = reverse("api.v1.whoami")
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_anonymous(client, settings):
    """Test response for anonymous users."""
    # Create some fake waffle objects
    Flag.objects.create(name="section_edit", authenticated=True)
    Flag.objects.create(name="flag_all", everyone=True)
    Flag.objects.create(name="flag_none", percent=0)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)
    Sample.objects.create(name="sample_never", percent=0)
    Sample.objects.create(name="sample_always", percent=100)

    url = reverse("api.v1.whoami")
    response = client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json() == {
        "username": None,
        "is_authenticated": False,
        "is_staff": False,
        "is_superuser": False,
        "is_beta_tester": False,
        "avatar_url": None,
        "waffle": {
            "flags": {
                "section_edit": False,
                "flag_all": True,
                "flag_none": False,
                "subscription": False,
                "subscription_banner": False,
            },
            "switches": {"switch_on": True, "switch_off": False},
            "samples": {"sample_always": True, "sample_never": False},
        },
        "is_subscriber": False,
        "email": None,
    }
    assert_no_cache_header(response)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "is_staff,is_superuser,is_beta_tester",
    [(False, False, False), (True, True, True)],
    ids=("muggle", "wizard"),
)
def test_whoami(
    user_client,
    wiki_user,
    wiki_user_github_account,
    beta_testers_group,
    is_staff,
    is_superuser,
    is_beta_tester,
):
    """Test responses for logged-in users."""
    # Create some fake waffle objects
    Flag.objects.create(name="section_edit", authenticated=True)
    Flag.objects.create(name="flag_all", everyone=True)
    Flag.objects.create(name="flag_none", percent=0, superusers=False)
    Switch.objects.create(name="switch_on", active=True)
    Switch.objects.create(name="switch_off", active=False)
    Sample.objects.create(name="sample_never", percent=0)
    Sample.objects.create(name="sample_always", percent=100)

    wiki_user.is_staff = is_staff
    wiki_user.is_superuser = is_superuser
    wiki_user.is_staff = is_staff
    if is_beta_tester:
        wiki_user.groups.add(beta_testers_group)
    wiki_user.save()
    url = reverse("api.v1.whoami")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert response.json() == {
        "username": wiki_user.username,
        "is_authenticated": True,
        "is_staff": is_staff,
        "is_superuser": is_superuser,
        "is_beta_tester": is_beta_tester,
        "avatar_url": wiki_user_github_account.get_avatar_url(),
        "waffle": {
            "flags": {
                "section_edit": True,
                "flag_all": True,
                "flag_none": False,
                "subscription": is_staff,
                "subscription_banner": is_staff,
            },
            "switches": {"switch_on": True, "switch_off": False},
            "samples": {"sample_always": True, "sample_never": False},
        },
        "is_subscriber": False,
        "email": "wiki_user@example.com",
    }
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_whoami_is_subscriber(
    user_client, wiki_user,
):
    """Test responses for logged-in users and whether they have an active
    subscription."""
    url = reverse("api.v1.whoami")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["is_subscriber"] is False

    UserSubscription.set_active(wiki_user, "abc123")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["is_subscriber"] is True

    UserSubscription.set_canceled(wiki_user, "abc123")
    response = user_client.get(url)
    assert response.status_code == 200
    assert response.json()["is_subscriber"] is False


@pytest.mark.django_db
def test_search_validation_problems(user_client):
    url = reverse("api.v1.search", args=["en-US"])

    # 'q' not present
    response = user_client.get(url)
    assert response.status_code == 400
    assert response.json()["error"] == "Search term 'q' must be set"

    # 'q' present but falsy
    response = user_client.get(url, {"q": ""})
    assert response.status_code == 400
    assert response.json()["error"] == "Search term 'q' must be set"

    # 'q' present but locale invalid
    response = user_client.get(url, {"q": "x", "locale": "xxx"})
    assert response.status_code == 400
    assert response.json()["error"] == "Not a valid locale code"

    # 'q' present but contains new line
    response = user_client.get(url, {"q": r"test\nsomething"})
    assert response.status_code == 400
    assert response.json()["q"] == ["Search term must not contain new line"]

    # 'q' present but exceeds max allowed characters
    response = user_client.get(url, {"q": "x" * (settings.ES_Q_MAXLENGTH + 1)})
    assert response.status_code == 400
    assert response.json()["q"] == [
        f"Ensure this field has no more than {settings.ES_Q_MAXLENGTH} characters."
    ]


class SearchViewTests(ElasticTestCase):
    fixtures = ElasticTestCase.fixtures + ["wiki/documents.json", "search/filters.json"]

    def test_search_basic(self):
        url = reverse("api.v1.search", args=["en-US"])
        response = self.client.get(url, {"q": "article"})
        assert response.status_code == 200
        assert response["content-type"] == "application/json"
        data = response.json()
        assert data["documents"]
        assert data["count"] == 4
        assert data["locale"] == "en-US"

        # Now search in a non-en-US locale
        response = self.client.get(url, {"q": "title", "locale": "fr"})
        assert response.status_code == 200
        assert response["content-type"] == "application/json"
        data = response.json()
        assert data["documents"]
        assert data["count"] == 5
        assert data["locale"] == "fr"


@pytest.mark.parametrize("http_method", ("put", "post", "delete", "options"))
def test_get_user_disallowed_methods(client, wiki_user, http_method):
    """
    HTTP methods other than GET and HEAD are not allowed on the api.v1.get_user
    endpoint.
    """
    url = reverse("api.v1.get_user", args=(wiki_user.username,))
    response = getattr(client, http_method)(url)
    assert response.status_code == 405
    assert_no_cache_header(response)


@pytest.mark.parametrize("case", ("upper", "lower"))
@pytest.mark.parametrize("http_method", ("get", "head"))
def test_get_existing_user(
    client, wiki_user, wiki_user_github_account, http_method, case
):
    """
    Test GET and HEAD on the api.v1.get_user endpoint for an existing user, and
    also that the username is case insensitive.
    """
    username = getattr(str, case)(wiki_user.username)
    url = reverse("api.v1.get_user", args=(username,))
    response = getattr(client, http_method)(url)
    assert response.status_code == 200
    assert response["content-type"] == "application/json"
    assert_no_cache_header(response)
    if http_method == "get":
        data = response.json()
        assert data["username"] == wiki_user.username
        assert data["avatar_url"] == wiki_user_github_account.get_avatar_url()
        for field in (
            "title",
            "fullname",
            "organization",
            "location",
            "timezone",
            "locale",
        ):
            assert data[field] == getattr(wiki_user, field)


@pytest.mark.parametrize("http_method", ("get", "head"))
def test_get_nonexisting_user(db, client, http_method):
    """
    Test GET and HEAD on the api.v1.get_user endpoint for a non-existing user.
    """
    url = reverse("api.v1.get_user", args=("nonexistent",))
    response = getattr(client, http_method)(url)
    assert response.status_code == 404
    assert_no_cache_header(response)


@pytest.mark.django_db
def test_bc_signal_happy_path(client, root_doc):
    url = reverse("api.v1.bc_signal")
    response = client.post(
        url,
        {
            "slug": root_doc.slug,
            "locale": root_doc.locale,
            "explanation": "My explanation",
            "feature": "Feet",
            "browsers": "One,Two",
            "supporting_material": "Extra things",
        },
    )
    assert response.status_code == 201

    bc_signal = BCSignal.objects.all().first()
    assert bc_signal.document == root_doc
    assert bc_signal.browsers == "One,Two"
    assert bc_signal.explanation == "My explanation"
    assert bc_signal.feature == "Feet"
    assert bc_signal.supporting_material == "Extra things"


@pytest.mark.django_db
def test_bc_signal_disabled(client, settings):
    settings.ENABLE_BCD_SIGNAL = False
    url = reverse("api.v1.bc_signal")
    response = client.post(url)
    assert response.status_code == 400


@pytest.mark.parametrize(
    "explanation", ("", "tooshort", "x" * 1001), ids=("empty", "too-short", "too-long")
)
@pytest.mark.django_db
def test_bc_signal_explanation_validation(client, root_doc, explanation):
    url = reverse("api.v1.bc_signal")
    data = {
        "slug": root_doc.slug,
        "locale": root_doc.locale,
        "explanation": explanation,
        "feature": "Feet",
        "browsers": "One,Two",
        "supporting_material": "Extra things",
    }
    response = client.post(url, data)
    assert response.status_code == 400
    assert response.json()["explanation"]


@pytest.mark.django_db
def test_bc_signal_document_validation(client):
    url = reverse("api.v1.bc_signal")
    response = client.post(
        url,
        {
            "slug": "xxx",
            "locale": "yyy",
            "explanation": "My explanation",
            "feature": "Feet",
            "browsers": "One,Two",
            "supporting_material": "Extra things",
        },
    )
    assert response.status_code == 400
    assert response.json() == ["Document not found"]


@pytest.mark.django_db
def test_bc_signal_http_method(client):
    url = reverse("api.v1.bc_signal")
    response = client.get(url)
    assert response.status_code == 405

    response = client.head(url)
    assert response.status_code == 405

    response = client.put(url)
    assert response.status_code == 405


@patch("kuma.api.v1.views.track_event")
@pytest.mark.django_db
@override_flag("subscription", True)
def test_send_subscriptions_feedback(track_event_mock_signals, client, settings):
    settings.GOOGLE_ANALYTICS_ACCOUNT = "UA-XXXX-1"
    settings.GOOGLE_ANALYTICS_TRACKING_RAISE_ERRORS = True

    response = client.post(
        reverse("api.v1.send_subscriptions_feedback"),
        content_type="application/json",
        data={"feedback": "my feedback"},
    )
    assert response.status_code == 204

    track_event_mock_signals.assert_called_with(
        CATEGORY_MONTHLY_PAYMENTS, ACTION_SUBSCRIPTION_FEEDBACK, "my feedback",
    )


@pytest.mark.django_db
@override_flag("subscription", True)
def test_send_subscriptions_feedback_failure(client, settings):
    response = client.post(
        reverse("api.v1.send_subscriptions_feedback"),
        content_type="application/json",
        data={},
    )

    assert response.status_code == 400
    assert response.content.decode(response.charset) == "no feedback"


@pytest.mark.django_db
@override_flag("subscription", True)
@patch("kuma.api.v1.views.create_stripe_customer_and_subscription_for_user")
def test_create_subscription_success(mock, user_client):
    response = user_client.post(
        reverse("api.v1.create_subscription"),
        content_type="application/json",
        data={"stripe_token": "tok_visa"},
    )

    assert response.status_code == 201


@pytest.mark.django_db
@override_flag("subscription", True)
def test_create_subscription_failure_without_login(client):
    response = client.post(reverse("api.v1.create_subscription"))
    assert response.status_code == 403


@pytest.mark.django_db
@override_flag("subscription", False)
def test_create_subscription_failure_with_disabled_waffle(user_client):
    response = user_client.post(reverse("api.v1.create_subscription"))
    assert response.status_code == 403
