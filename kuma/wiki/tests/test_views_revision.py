"""Tests for kuma.wiki.views.revision."""
import json
from datetime import datetime
from urllib.parse import urlencode

import pytest
from django.conf import settings
from rest_framework.authtoken.models import Token

from kuma.core.tests import assert_no_cache_header, assert_shared_cache_header
from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams

from ..models import Document, Revision
from ..views.utils import get_last_modified_header


@pytest.fixture
def doc_with_macros(wiki_user):
    """A top-level English document containing multiple macro calls."""
    doc_with_macros = Document.objects.create(
        locale="en-US", slug="Macros", title="Macros Document"
    )
    Revision.objects.create(
        document=doc_with_macros,
        creator=wiki_user,
        content='{{M1("x")}}{{M1("y")}}{{M2("z")}}',
        title="Macros Document",
        created=datetime(2020, 1, 11, 10, 15),
    )
    return doc_with_macros


@pytest.fixture
def wiki_user_2_token(wiki_user_2):
    return Token.objects.create(user=wiki_user_2)


@pytest.mark.parametrize("raw", [True, False])
def test_compare_revisions(edit_revision, client, raw):
    """Comparing two valid revisions of the same document works."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()
    params = {"from": first_revision.id, "to": edit_revision.id}
    if raw:
        params["raw"] = "1"
    url = urlparams(reverse("wiki.compare_revisions", args=[doc.slug]), **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response["X-Robots-Tag"] == "noindex"
    assert_shared_cache_header(response)


@pytest.mark.parametrize("raw", [True, False])
def test_compare_translation(trans_revision, client, raw):
    """A localized revision can be compared to an English source revision."""
    fr_doc = trans_revision.document
    en_revision = trans_revision.based_on
    en_doc = en_revision.document
    assert en_doc != fr_doc
    params = {"from": en_revision.id, "to": trans_revision.id}
    if raw:
        params["raw"] = "1"
    url = urlparams(
        reverse("wiki.compare_revisions", args=[fr_doc.slug], locale=fr_doc.locale),
        **params,
    )

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response["X-Robots-Tag"] == "noindex"
    assert_shared_cache_header(response)


@pytest.mark.parametrize("raw", [True, False])
def test_compare_revisions_without_tidied_content(edit_revision, client, raw):
    """Comparing revisions without tidied content displays a wait message."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()

    # update() to skip the tidy_revision_content post_save signal handler
    ids = [first_revision.id, edit_revision.id]
    Revision.objects.filter(id__in=ids).update(tidied_content="")

    params = {"from": first_revision.id, "to": edit_revision.id}
    if raw:
        params["raw"] = "1"
    url = urlparams(reverse("wiki.compare_revisions", args=[doc.slug]), **params)

    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert b"Please refresh this page in a few minutes." in response.content


@pytest.mark.parametrize(
    "id1,id2", [("1e309", "1e309"), ("", "invalid"), ("invalid", "")]
)
def test_compare_revisions_invalid_ids(root_doc, client, id1, id2):
    """Comparing badly-formed revision parameters return 404, not error."""
    url = urlparams(
        reverse("wiki.compare_revisions", args=[root_doc.slug]),
        **{"from": id1, "to": id2},
    )
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404


@pytest.mark.parametrize("param", ["from", "to"])
def test_compare_revisions_only_one_param(create_revision, client, param):
    """If a compare query parameter is missing, a 404 is returned."""
    doc = create_revision.document
    url = urlparams(
        reverse("wiki.compare_revisions", args=[doc.slug]),
        **{param: create_revision.id},
    )
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404


def test_compare_revisions_wrong_document(edit_revision, client):
    """If the revision is for the wrong document, a 404 is returned."""
    doc = edit_revision.document
    first_revision = doc.revisions.first()
    other_doc = Document.objects.create(
        locale="en-US", slug="Other", title="Other Document"
    )
    url = urlparams(
        reverse("wiki.compare_revisions", args=[other_doc.slug]),
        **{"from": first_revision.id, "to": edit_revision.id},
    )
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404


@pytest.mark.parametrize("http_method", ("put", "delete"))
def test_revision_api_disallowed_methods(client, http_method):
    """
    The wiki.revision_api endpoint does not support HTTP methods other than
    GET, HEAD, OPTIONS, and POST.
    """
    url = reverse("wiki.revision_api", args=["Web/HTML"], locale="fr")
    response = getattr(client, http_method)(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 405
    assert_no_cache_header(response)


def test_revision_api_ensure_wiki_domain(client):
    """The wiki.revision_api endpoint is only supported on the wiki domain."""
    url = reverse("wiki.revision_api", args=["Web/HTML"], locale="fr")
    response = client.get(url)
    assert response.status_code == 301
    assert response["Location"].startswith(settings.WIKI_SITE_URL)
    assert_no_cache_header(response)


def test_revision_api_404(db, client):
    """
    The wiki.revision_api endpoint returns 404 if the document does not exist.
    """
    url = reverse("wiki.revision_api", args=["does/not/exist"], locale="de")
    response = client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 404
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    "qs,expected",
    (
        ("?macros=m1,m2", 'Please specify a "mode" query parameter.'),
        ("?mode=sing", 'The "mode" query parameter must be "render" or "remove".'),
        (
            "?mode=remove",
            (
                "Please specify one or more comma-separated macro names "
                'via the "macros" query parameter.'
            ),
        ),
    ),
    ids=("missing-mode", "invalid-mode", "missing-macros"),
)
def test_revision_api_get_400(doc_with_macros, client, qs, expected):
    """The wiki.revision_api endpoint returns 400 for bad GET requests."""
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )
    response = client.get(url + qs, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 400
    assert response.content.decode() == expected
    assert_no_cache_header(response)


def test_revision_api_post_unauthorized(doc_with_macros, client):
    """
    The wiki.revision_api endpoint returns 403 for unauthorized POST requests.
    """
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )
    data = dict(content="yada yada yada")
    response = client.post(url, data=data, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 403
    assert_no_cache_header(response)


def test_revision_api_post_400(doc_with_macros, wiki_user_2_token, client):
    """The wiki.revision_api endpoint returns 400 for bad POST requests."""
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )
    response = client.post(
        url,
        content_type="text/plain",
        HTTP_HOST=settings.WIKI_HOST,
        HTTP_AUTHORIZATION=f"Token {wiki_user_2_token.key}",
    )
    assert response.status_code == 400
    assert response.content.decode() == (
        'POST body must be of type "application/json", '
        '"application/x-www-form-urlencoded", or "multipart/form-data".'
    )
    assert_no_cache_header(response)


@pytest.mark.parametrize(
    "qs,expected",
    (
        ("", '{{M1("x")}}{{M1("y")}}{{M2("z")}}'),
        ("?mode=remove&macros=m1", '{{M2("z")}}'),
        ("?mode=remove&macros=m1,m2", ""),
        ("?mode=remove&macros=junk", '{{M1("x")}}{{M1("y")}}{{M2("z")}}'),
        ("?mode=render&macros=junk", '{{M1("x")}}{{M1("y")}}{{M2("z")}}'),
    ),
    ids=("no-change", "remove-single", "remove-multiple", "remove-miss", "render-miss"),
)
def test_revision_api_get(doc_with_macros, client, constance_config, qs, expected):
    """
    The wiki.revision_api endpoint returns revised raw HTML for GET requests.
    """
    constance_config.KUMASCRIPT_TIMEOUT = 1
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )
    response = client.get(url + qs, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    assert response.content.decode() == expected
    assert_no_cache_header(response)
    assert response["X-Frame-Options"] == "deny"
    assert response["X-Robots-Tag"] == "noindex"
    assert response["Last-Modified"] == get_last_modified_header(
        doc_with_macros.current_revision.created
    )


@pytest.mark.parametrize("case", ("json", "form-data", "form-urlencoded"))
def test_revision_api_post(
    doc_with_macros, wiki_user_2, wiki_user_2_token, client, case
):
    """
    The wiki.revision_api endpoint returns 201 for successful POST requests.
    """
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )
    kwargs = dict(
        data=dict(content="yada"),
        HTTP_HOST=settings.WIKI_HOST,
        HTTP_AUTHORIZATION=f"Token {wiki_user_2_token.key}",
    )
    if case == "json":
        kwargs["data"] = json.dumps(kwargs["data"])
        kwargs.update(content_type="application/json")
    elif case == "form-urlencoded":
        kwargs["data"] = urlencode(kwargs["data"])
        kwargs.update(content_type="application/x-www-form-urlencoded")

    response = client.post(url, **kwargs)
    doc_with_macros.refresh_from_db()
    new_rev = doc_with_macros.current_revision
    assert new_rev.creator == wiki_user_2
    assert new_rev.content == "yada"
    assert response.status_code == 201
    assert response["Location"].endswith(
        reverse(
            "wiki.revision",
            args=(doc_with_macros.slug, new_rev.id),
            locale=doc_with_macros.locale,
        )
    )
    assert response.content.decode() == "yada"
    assert response["Last-Modified"] == get_last_modified_header(new_rev.created)
    assert_no_cache_header(response)


def test_revision_api_conditional_post(
    doc_with_macros, wiki_user_2, wiki_user_2_token, constance_config, client
):
    """
    The wiki.revision_api endpoint returns 201 for successful, and 412 for
    failed, conditional POST requests.
    """
    constance_config.KUMASCRIPT_TIMEOUT = 1
    url = reverse(
        "wiki.revision_api", args=[doc_with_macros.slug], locale=doc_with_macros.locale
    )

    # First let's get some revised content and the Last-Modified header.
    response = client.get(url + "?mode=remove&macros=m1", HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    revised_content = response.content.decode()
    assert revised_content == '{{M2("z")}}'
    last_modified_from_get = response["Last-Modified"]

    # Let's POST the revised content, but with the condition that no one else
    # has created a new revision for the document since we performed our GET.
    response = client.post(
        url,
        data=dict(content=revised_content),
        HTTP_HOST=settings.WIKI_HOST,
        HTTP_IF_UNMODIFIED_SINCE=last_modified_from_get,
        HTTP_AUTHORIZATION=f"Token {wiki_user_2_token.key}",
    )
    doc_with_macros.refresh_from_db()
    new_rev = doc_with_macros.current_revision
    assert new_rev.creator == wiki_user_2
    assert new_rev.content == revised_content
    assert response.status_code == 201
    assert response["Location"].endswith(
        reverse(
            "wiki.revision",
            args=(doc_with_macros.slug, new_rev.id),
            locale=doc_with_macros.locale,
        )
    )
    assert response.content.decode() == revised_content
    assert_no_cache_header(response)
    assert response["Last-Modified"] == get_last_modified_header(new_rev.created)

    # This time we're someone else, holding the same "last_modified_from_get"
    # value, who also wants to conditionally revise the document, but since
    # it has changed, the condition will not be satisfied and the POST will
    # fail.
    response = client.post(
        url,
        data=dict(content="yada"),
        HTTP_HOST=settings.WIKI_HOST,
        HTTP_IF_UNMODIFIED_SINCE=last_modified_from_get,
        HTTP_AUTHORIZATION=f"Token {wiki_user_2_token.key}",
    )
    assert response.status_code == 412
    assert_no_cache_header(response)
