import json
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils.timezone import make_aware
from pyquery import PyQuery as pq
from pytz import AmbiguousTimeError

from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse

from . import normalize_html
from ..feeds import DocumentJSONFeedGenerator
from ..models import Document, Revision


def test_l10n_updates_no_updates(trans_doc, client):
    """When translations are up-to-date, l10n-updates feed is empty."""
    feed_url = reverse(
        "wiki.feeds.l10n_updates", locale=trans_doc.locale, kwargs={"format": "json"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 0  # No entries, translation is up to date


def test_l10n_updates_parent_updated(trans_doc, edit_revision, client):
    """Out-of-date translations appear in the l10n-updates feed."""
    feed_url = reverse(
        "wiki.feeds.l10n_updates", locale=trans_doc.locale, kwargs={"format": "json"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 1
    assert trans_doc.get_absolute_url() in data[0]["link"]


def test_l10n_updates_include_campaign(
    trans_doc, create_revision, edit_revision, client
):
    """Translation URLs include GA campaign data."""
    feed_url = reverse(
        "wiki.feeds.l10n_updates", locale=trans_doc.locale, kwargs={"format": "rss"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 1
    desc_text = pq(items).find("description").text()
    desc_html = pq(desc_text)  # Description is encoded HTML
    links = desc_html.find("a")
    assert len(links) == 3
    for link in links:
        href = link.attrib["href"]
        querystring = parse_qs(urlparse(href).query)
        assert querystring["utm_campaign"] == ["feed"]
        assert querystring["utm_medium"] == ["rss"]
        assert querystring["utm_source"] == ["developer.mozilla.org"]


create_revision_rss = normalize_html(
    """
<h3>Created by:</h3>
  <p>wiki_user</p>
<h3>Content changes:</h3>
  &lt;p&gt;Getting started...&lt;/p&gt;
<table border="0" width="80%">
  <tr>
    <td><a href="/en-US/docs/Root?utm_campaign=feed&utm_medium=rss&\
utm_source=developer.mozilla.org">View Page</a></td>
    <td><a href="/en-US/docs/Root$edit?utm_campaign=feed&\
utm_medium=rss&utm_source=developer.mozilla.org">Edit Page</a></td>
    <td><a href="/en-US/docs/Root$history?utm_campaign=feed&\
utm_medium=rss&utm_source=developer.mozilla.org">History</a></td>
  </tr>
</table>"""
)

# TODO: Investigate encoding issue w/ <h3> Content changes
edit_revision_rss_template = normalize_html(
    """
<h3>Edited by:</h3>
  <p>wiki_user</p>
<h3>Comment:</h3>
  <p>Done with initial version.</p>
&lt;h3&gt;Content changes:&lt;/h3&gt;
<table class="diff" id="difflib_chg_to%(diff_id)s__top"
       cellspacing="0" cellpadding="0" rules="groups" >
  <colgroup></colgroup>
  <colgroup></colgroup>
  <colgroup></colgroup>
  <colgroup></colgroup>
  <colgroup></colgroup>
  <colgroup></colgroup>
  <thead>
    <tr>
      <th class="diff_next"><br /></th>
      <th colspan="2" class="diff_header">Revision %(from_id)s</th>
      <th class="diff_next"><br /></th>
      <th colspan="2" class="diff_header">Revision %(to_id)s</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="diff_next" id="difflib_chg_to%(diff_id)s__0">
        <a href="#difflib_chg_to%(diff_id)s__top">t</a>
      </td>
      <td class="diff_header" id="from%(diff_id)s_8">8</td>
      <td nowrap="nowrap">
        <span class="diff_sub">
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Getting&nbsp;started...
        </span>
      </td>
      <td class="diff_next"><a href="#difflib_chg_to%(diff_id)s__top">t</a></td>
      <td class="diff_header" id="to%(diff_id)s_8">8</td>
      <td nowrap="nowrap">
        <span class="diff_add">
          &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The&nbsp;root&nbsp;document.
        </span>
      </td>
    </tr>
  </tbody>
</table>
<table border="0" width="80%%">
  <tr>
    <td>
      <a href="/en-US/docs/Root?utm_campaign=feed&utm_medium=rss&\
utm_source=developer.mozilla.org">View Page</a>
    </td>
    <td>
      <a href="/en-US/docs/Root$edit?utm_campaign=feed&utm_medium=rss&\
utm_source=developer.mozilla.org">Edit Page</a>
    </td>
    <td>
      <a href="/en-US/docs/Root$compare?from=%(from_id)s&to=%(to_id)s&\
utm_campaign=feed&utm_medium=rss&utm_source=developer.mozilla.org">
        Show comparison
      </a>
    </td>
    <td>
      <a href="/en-US/docs/Root$history?utm_campaign=feed&utm_medium=rss\
&utm_source=developer.mozilla.org">History</a>
    </td>
  </tr>
</table>"""
)


def extract_description(feed_item):
    """Extract the description and diff ID (if set) from a feed item."""
    desc_text = pq(feed_item).find("description").text()
    desc = pq(desc_text)
    table = desc.find("table.diff")
    if table:
        # Format is difflib_chg_to[DIFF ID]__top
        assert len(table) == 1
        table_id = table[0].attrib["id"]
        prefix = "difflib_chg_to"
        suffix = "__top"
        assert table_id.startswith(prefix)
        assert table_id.endswith(suffix)
        diff_id = int(table_id[len(prefix) : -len(suffix)])
    else:
        diff_id = None
    return normalize_html(desc_text), diff_id


def test_recent_revisions(create_revision, edit_revision, client):
    """The revisions feed includes recent revisions."""
    feed_url = reverse("wiki.feeds.recent_revisions", kwargs={"format": "rss"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 2
    desc1, diff_id1 = extract_description(items[0])
    assert desc1 == create_revision_rss
    assert diff_id1 is None

    desc2, diff_id2 = extract_description(items[1])
    expected = edit_revision_rss_template % {
        "from_id": create_revision.id,
        "to_id": edit_revision.id,
        "diff_id": diff_id2,
    }
    assert desc2 == expected


def test_recent_revisions_pages(create_revision, edit_revision, client):
    """The revisions feed can be paginated."""
    feed_url = reverse("wiki.feeds.recent_revisions", kwargs={"format": "rss"})
    resp = client.get(feed_url, {"limit": 1})
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 1
    desc_text, diff_id = extract_description(items[0])
    expected = edit_revision_rss_template % {
        "from_id": create_revision.id,
        "to_id": edit_revision.id,
        "diff_id": diff_id,
    }
    assert desc_text == expected

    resp = client.get(feed_url, {"limit": 1, "page": 2})
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 1
    desc_text2, diff_id2 = extract_description(items[0])
    assert desc_text2 == create_revision_rss


def test_recent_revisions_limit_0(edit_revision, client):
    """
    For the revisions feed, a limit of 0 gets no results.

    TODO: the limit should probably be MAX_FEED_ITEMS instead, and applied
    before the start and finish positions are picked.
    """
    feed_url = reverse("wiki.feeds.recent_revisions", kwargs={"format": "rss"})
    resp = client.get(feed_url, {"limit": 0})
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 0


def test_recent_revisions_all_locales(trans_edit_revision, client, settings):
    """The ?all_locales parameter returns mixed locales (bug 869301)."""
    host = "example.com"
    settings.ALLOWED_HOSTS.append(host)
    feed_url = reverse("wiki.feeds.recent_revisions", kwargs={"format": "rss"})
    resp = client.get(
        feed_url, {"all_locales": ""}, HTTP_HOST=host, HTTP_X_FORWARDED_PROTO="https"
    )
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 4

    # Test that links use host domain
    actual_links = [pq(item).find("link").text() for item in items]
    actual_domains = [urlparse(link).netloc for link in actual_links]
    assert actual_domains == [host] * 4

    # Test that links are a mix of en-US and translated documents
    trans_doc = trans_edit_revision.document
    root_doc = trans_doc.parent
    expected_paths = [
        root_doc.get_absolute_url(),
        trans_doc.get_absolute_url(),
        root_doc.get_absolute_url(),
        trans_doc.get_absolute_url(),
    ]
    actual_paths = [urlparse(link).path for link in actual_links]
    assert expected_paths == actual_paths


def test_recent_revisions_diff_includes_tags(create_revision, client):
    """The revision feed includes document tags and editorial flags."""
    new_revision = create_revision.document.revisions.create(
        title=create_revision.title,
        content=create_revision.content,
        creator=create_revision.creator,
        tags='"NewTag"',
    )
    new_revision.review_tags.add("editorial")
    feed_url = reverse("wiki.feeds.recent_revisions", kwargs={"format": "rss"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 2
    desc1, desc2 = [pq(item).find("description").text() for item in items]
    assert "Edited" not in desc1  # Created revision
    assert "Edited" in desc2  # New revision
    assert "<h3>Tag changes:</h3>" in desc2
    assert (
        '<span class="diff_add" style="background-color: #afa; '
        'text-decoration: none;">"NewTag"</span>'
    ) in desc2
    assert "<h3>Review changes:</h3>" in desc2
    assert (
        '<span class="diff_add" style="background-color: #afa; '
        'text-decoration: none;">editorial</span>'
    ) in desc2


def test_recent_revisions_feed_ignores_render(edit_revision, client):
    """Re-rendering a document does not update the feed."""
    feed_url = reverse("wiki.feeds.recent_documents", args=(), kwargs={"format": "rss"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    start_content = resp.content

    # Re-render document, RSS feed doesn't change
    edit_revision.document.render(cache_control="no-cache")
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert resp.content == start_content

    # Create a new edit, RSS feed changes
    edit_revision.document.revisions.create(
        title=edit_revision.title,
        content=edit_revision.content + "\n<p>New Line</p>",
        creator=edit_revision.creator,
    )
    resp = client.get(feed_url)
    assert resp.content != start_content


def test_recent_revisions_feed_omits_docs_without_rev(edit_revision, client):
    """Documents without a current revision are omitted from the feed."""
    feed_url = reverse("wiki.feeds.recent_documents", args=(), kwargs={"format": "rss"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 1

    Document.objects.create(locale="en-US", slug="NoCurrentRev", title="No Current Rev")
    resp = client.get(feed_url)
    assert resp.status_code == 200
    feed = pq(resp.content)
    items = feed.find("item")
    assert len(items) == 1


@pytest.mark.parametrize("locale", ("en-US", "fr"))
def test_recent_revisions_feed_filter_by_locale(locale, trans_edit_revision, client):
    """The recent revisions feed can be filtered by locale."""
    feed_url = reverse(
        "wiki.feeds.recent_revisions", locale=locale, kwargs={"format": "json"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 2
    for item in data:
        path = urlparse(item["link"]).path
        assert path.startswith("/" + locale + "/")


@pytest.mark.parametrize("locale", ("en-US", "fr"))
def test_recent_documents_feed_filter_by_locale(locale, trans_edit_revision, client):
    """The recent documents feed can be filtered by locale."""
    feed_url = reverse(
        "wiki.feeds.recent_documents", locale=locale, kwargs={"format": "json"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 1
    path = urlparse(data[0]["link"]).path
    assert path.startswith("/" + locale + "/")


def test_recent_documents_atom_feed(root_doc, client):
    """The recent documents feed can be formatted as an Atom feed."""
    feed_url = reverse("wiki.feeds.recent_documents", kwargs={"format": "atom"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert resp["Content-Type"] == "application/atom+xml; charset=utf-8"


def test_recent_documents_as_jsonp(root_doc, client):
    """The recent documents feed can be called with a JSONP wrapper."""
    feed_url = reverse("wiki.feeds.recent_documents", kwargs={"format": "json"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    raw_json = resp.content

    resp = client.get(feed_url, {"callback": "jsonp_callback"})
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    wrapped = resp.content
    assert wrapped == b"jsonp_callback(%s)" % raw_json

    # Invalid callback names are rejected
    resp = client.get(feed_url, {"callback": "try"})
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    assert resp.content == raw_json


def test_recent_documents_optional_items(create_revision, client, settings):
    """The recent documents JSON feed includes some items if set."""
    feed_url = reverse("wiki.feeds.recent_documents", kwargs={"format": "json"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 1
    assert data[0]["author_avatar"] == settings.DEFAULT_AVATAR
    assert "summary" not in data[0]

    create_revision.summary = "The summary"
    create_revision.save()
    resp = client.get(feed_url)
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert data[0]["summary"] == "The summary"


def test_recent_documents_feed_filter_by_tag(edit_revision, client):
    """The recent documents feed can be filtered by tag."""
    feed_url = reverse(
        "wiki.feeds.recent_documents", kwargs={"format": "json", "tag": "TheTag"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 0

    edit_revision.document.revisions.create(
        title=edit_revision.title,
        content=edit_revision.content,
        creator=edit_revision.creator,
        tags='"TheTag"',
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data) == 1


@pytest.mark.tags
def test_feeds_update_after_doc_tag_change(client, wiki_user, root_doc):
    """Tag feeds should be updated after document tags change"""
    tags1 = ["foo", "bar", "js"]
    tags2 = ["lorem", "ipsum"]
    # Create a revision with some tags
    Revision.objects.create(document=root_doc, tags=",".join(tags1), creator=wiki_user)

    # Create another revision with some other tags
    Revision.objects.create(document=root_doc, tags=",".join(tags2), creator=wiki_user)

    # Check document is latest tags feed
    for tag in tags2:
        response = client.get(
            reverse("wiki.feeds.recent_documents", args=["atom", tag]), follow=True
        )
        assert response.status_code == 200
        assert root_doc.title in response.content.decode(response.charset)

    # Check document is not in the previous tags feed
    for tag in tags1:
        response = client.get(
            reverse("wiki.feeds.recent_documents", args=["atom", tag]), follow=True
        )
        assert response.status_code == 200
        assert root_doc.title not in response.content.decode(response.charset)


def test_recent_documents_handles_ambiguous_time(root_doc, client):
    """The recent_documents feed handles times during DST transition."""
    ambiguous = datetime(2017, 11, 5, 1, 8, 42)
    with pytest.raises(AmbiguousTimeError):
        make_aware(ambiguous)
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=root_doc.current_revision.creator,
        content="<p>Happy Daylight Savings Time!</p>",
        title=root_doc.title,
        created=ambiguous,
    )
    feed_url = reverse("wiki.feeds.recent_documents", kwargs={"format": "json"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 1


def test_list_review(edit_revision, client):
    """The documents needing review feed shows documents needing any review."""
    feed_url = reverse("wiki.feeds.list_review", kwargs={"format": "json"})
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 0

    edit_revision.review_tags.add("editorial")
    resp = client.get(feed_url)
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data) == 1


def test_list_review_tag(edit_revision, client):
    """The documents needing editorial review feed works."""
    feed_url = reverse(
        "wiki.feeds.list_review_tag", kwargs={"format": "json", "tag": "editorial"}
    )
    resp = client.get(feed_url)
    assert resp.status_code == 200
    assert_shared_cache_header(resp)
    data = json.loads(resp.content)
    assert len(data) == 0

    edit_revision.review_tags.add("editorial")
    resp = client.get(feed_url)
    assert resp.status_code == 200
    data = json.loads(resp.content)
    assert len(data) == 1


def test_documentjsonfeedgenerator_encode():
    """
    The DocumentJSONFeedGenerator encodes datetimes, but no other extra types.

    TODO: The function should raise TypeError instead of returning None.
    """
    generator = DocumentJSONFeedGenerator("Title", "/feed", "Description")
    dt = datetime(2017, 12, 21, 22, 25)
    assert generator._encode_complex(dt) == "2017-12-21T22:25:00"
    assert generator._encode_complex(dt.date()) is None
