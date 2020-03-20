from datetime import datetime
from unittest import mock

import pytest
from django.db import IntegrityError

from kuma.wiki.constants import REDIRECT_CONTENT
from kuma.wiki.models import Document, DocumentTag, Revision

from ..storage import Storage


@pytest.mark.parametrize(
    "data_name,param_list",
    (
        ("document_children", ("locale", "slug")),
        ("document_metadata", ("locale", "slug")),
        ("document_history", ("locale", "slug")),
        ("document_redirect", ("locale", "slug")),
        ("revision_html", ("path",)),
    ),
    ids=[
        "document_children",
        "document_metadata",
        "document_history",
        "document_redirect",
        "revision_html",
    ],
)
def test_local_storage(data_name, param_list):
    """Local storage objects are None when unset, return the saved value."""
    storage = Storage()
    getter = getattr(storage, "get_" + data_name)
    setter = getattr(storage, "save_" + data_name)
    assert getter(*param_list) is None
    value = data_name + " value"
    setter(data=value, *param_list)
    assert getter(*param_list) == value


@pytest.mark.django_db
def test_get_document_missing():
    assert Storage().get_document("en-US", "Test") is None


def test_get_document_present(simple_doc):
    doc = Storage().get_document("en-US", "Root")
    assert doc.locale == "en-US"
    assert doc.slug == "Root"


@pytest.mark.django_db
def test_save_document():
    data = {
        "id": 100,
        "locale": "en-US",
        "modified": datetime(2016, 11, 9, 9, 40),
        "slug": "Test",
        "tags": [],
        "title": "Test Document",
        "uuid": "d269d6c8-0759-49bc-92ab-03f126e73809",
    }
    Storage().save_document(data)
    document = Document.objects.get(locale="en-US", slug="Test")
    assert document.title == "Test Document"
    assert str(document.uuid) == data["uuid"]


@pytest.mark.django_db
def test_save_document_tags():
    """Tags are created and attached to the new document."""
    data = {
        "id": 101,
        "locale": "en-US",
        "modified": datetime(2016, 11, 15, 9, 31),
        "slug": "Test",
        "tags": ["NeedsTranslation"],
        "title": "Test Document",
    }
    Storage().save_document(data)
    document = Document.objects.get(locale="en-US", slug="Test")
    assert document.title == "Test Document"
    assert list(document.tags.names()) == ["NeedsTranslation"]


@pytest.mark.django_db
def test_save_document_dupe_tags():
    """
    Duplicate tags are de-duped on document save.

    This may not be needed now that bug 1293749 is fixed.
    """
    data = {
        "id": 101,
        "locale": "en-US",
        "modified": datetime(2016, 11, 15, 9, 31),
        "slug": "Test",
        "tags": ["NeedsTranslation", "needstranslation"],
        "title": "Test Document",
    }
    Storage().save_document(data)
    document = Document.objects.get(locale="en-US", slug="Test")
    assert document.title == "Test Document"
    assert list(document.tags.names()) == ["NeedsTranslation"]


def test_save_document_update_existing(simple_doc):
    """An existing document gets new scraped tags."""
    assert list(simple_doc.tags.names()) == []
    data = {
        "id": simple_doc.id,
        "locale": "en-US",
        "slug": "Root",
        "tags": ["SuperTag"],
    }
    Storage().save_document(data)
    document = Document.objects.get(id=simple_doc.id)
    assert list(document.tags.names()) == ["SuperTag"]


def test_save_document_update_existing_to_redirect(simple_doc):
    """An existing document that has been moved is moved locally."""
    data = {"locale": "en-US", "slug": "Root", "redirect_to": "/en-US/docs/SuperTest"}
    redirect_html = REDIRECT_CONTENT % {
        "href": data["redirect_to"],
        "title": "Root Document",
    }
    Storage().save_document(data)
    document = Document.objects.get(id=simple_doc.id)
    assert document.is_redirect
    assert document.html == redirect_html


def test_save_document_new_doc_colliding_id(simple_doc):
    """An existing document can have a different ID than remote doc."""
    new_data = {
        "id": simple_doc.id,
        "locale": "en-US",
        "slug": "NewDoc",
        "title": "New Document",
    }
    Storage().save_document(new_data)
    new_doc = Document.objects.get(locale="en-US", slug="NewDoc")
    assert new_doc.id != simple_doc.id


@pytest.mark.django_db
def test_save_document_integrity_error():
    """Can save ca/docs/Project:Quant_a, despite IntegrityError."""
    en_root_doc = Document.objects.create(locale="en-US", slug="MDN", title="MDN")
    en_doc = Document.objects.create(
        locale="en-US", slug="MDN/About", title="About MDN", parent_topic=en_root_doc
    )
    ca_id = 1000
    assert not Document.objects.filter(id=ca_id).exists()
    ca_data = {
        "locale": "ca",
        "slug": "Project:Quant_a",
        "title": "Quant a",
        "parent": en_doc,
        "id": ca_id,
    }

    def ca_weirdness(**data):
        ca_doc = Document()
        for name, value in data.items():
            setattr(ca_doc, name, value)
        ca_doc.save()
        raise IntegrityError("ID in use")

    with mock.patch("kuma.scrape.storage.Document.objects.create") as mcreate:
        mcreate.side_effect = ca_weirdness
        Storage().save_document(ca_data)
    mcreate.assert_called_once_with(**ca_data)
    ca_doc = Document.objects.get(locale="ca", slug="Project:Quant_a")
    assert ca_doc.title == "Quant a"
    assert ca_doc.parent == en_doc


def test_get_revision_existing(root_doc):
    stored = Storage().get_revision(root_doc.current_revision_id)
    assert stored == root_doc.current_revision


@pytest.mark.django_db
def test_get_revision_missing():
    rev_id = 666
    assert not Revision.objects.filter(id=rev_id).exists()
    assert Storage().get_revision(rev_id) is None


def test_save_revision_current(simple_doc, simple_user):
    """Creating the current revision updates the associated document."""
    assert not simple_doc.html
    data = {
        "id": 1000,
        "creator": simple_user,
        "document": simple_doc,
        "slug": "Test",
        "title": "Test Document",
        "created": datetime(2016, 11, 15, 16, 49),
        "is_current": True,
        "comment": "Frist Post!",
        "tags": ["One", "Two", "Three"],
        "content": "<p>My awesome content.</p>",
    }
    Storage().save_revision(data)
    rev = Revision.objects.get(id=1000)
    assert rev.document == simple_doc
    assert rev.document.html == rev.content
    assert rev.creator == simple_user
    assert rev.tags == '"One" "Two" "Three"'
    assert rev.content == "<p>My awesome content.</p>"


def test_save_revision_not_current(root_doc, simple_user):
    """Creating an older revision does not update the associated document."""
    old_content = root_doc.html
    assert old_content
    data = {
        "id": 1000,
        "creator": simple_user,
        "document": root_doc,
        "slug": "Test",
        "title": "Test Document",
        "created": datetime(2014, 1, 1),
        "is_current": False,
        "comment": "Frist Post!",
        "tags": [],
        "content": "<p>My awesome content.</p>",
    }
    Storage().save_revision(data)
    rev = Revision.objects.get(id=1000)
    assert rev.document == root_doc
    assert rev.document.html == old_content
    assert rev.creator == simple_user
    assert rev.tags == ""
    assert rev.content == "<p>My awesome content.</p>"


def test_save_revision_duplicate_tags(simple_doc, simple_user):
    """
    A current revision with duplicate tags does not create dupes on the doc.

    Historical revisions will have these duplicate tags, even though
    bug 1293749 is fixed, because they are stored as strings.
    """
    data = {
        "id": 1001,
        "creator": simple_user,
        "document": simple_doc,
        "slug": "Test",
        "title": "Test Document",
        "created": datetime(2016, 11, 16, 11, 27),
        "is_current": True,
        "comment": "Frist Post!",
        "tags": ["one", "two", "One", "Two"],
        "content": "<p>My awesome content.</p>",
    }
    Storage().save_revision(data)
    rev = Revision.objects.get(id=1001)
    assert rev.document == simple_doc
    assert rev.creator == simple_user
    assert rev.tags == '"One" "Two"'
    assert sorted(rev.document.tags.names()) == ["One", "Two"]


def test_save_revision_existing_tags(simple_doc, simple_user):
    """Existing tags are reused when saving a current revision."""
    DocumentTag.objects.create(name="One")
    DocumentTag.objects.create(name="Two")
    data = {
        "id": 1002,
        "creator": simple_user,
        "document": simple_doc,
        "slug": "Test",
        "title": "Test Document",
        "created": datetime(2016, 12, 19, 13, 52),
        "is_current": True,
        "comment": "Frist Post!",
        "tags": ["one", "two"],
        "content": "<p>My awesome content.</p>",
    }
    Storage().save_revision(data)
    rev = Revision.objects.get(id=1002)
    assert rev.document == simple_doc
    assert rev.creator == simple_user
    assert rev.tags == '"One" "Two"'
    assert sorted(rev.document.tags.names()) == ["One", "Two"]


def test_save_revision_no_content_review_tags(simple_doc, simple_user):
    """A revision may have no content but include review tags."""
    data = {
        "id": 1003,
        "creator": simple_user,
        "document": simple_doc,
        "slug": "Test",
        "title": "Test Document",
        "created": datetime(2016, 12, 19, 13, 52),
        "is_current": True,
        "tags": [],
        "review_tags": ["technical"],
        "localization_tags": ["inprogress"],
    }
    Storage().save_revision(data)
    rev = Revision.objects.get(id=1003)
    assert rev.document == simple_doc
    assert rev.creator == simple_user
    assert rev.content == ""
    assert list(rev.review_tags.names()) == ["technical"]
    assert list(rev.localization_tags.names()) == ["inprogress"]


@pytest.mark.django_db
def test_get_user_missing():
    assert Storage().get_user("missing") is None


def test_get_user_present(simple_user):
    user = Storage().get_user(simple_user.username)
    assert user == simple_user


def test_save_user(django_user_model):
    data = {
        "username": "JoeDeveloper",
        "fullname": "Joe Developer",
        "title": "Web Developer",
        "organization": "Acme, Inc.",
        "location": "Springfield, USA",
        "irc_nickname": "joedev",
        "twitter_url": "http://twitter.com/joedev1999",
        "github_url": "https://github.com/joedev1999",
        "stackoverflow_url": "http://stackoverflow.com/users/1/joedev1999",
        "linkedin_url": "http://www.linkedin.com/in/joedev1999",
        "mozillians_url": "http://mozillians.org/u/joedev/",
        "date_joined": datetime(1999, 1, 1, 10, 40, 23),
    }
    Storage().save_user(data)
    user = django_user_model.objects.get(username="JoeDeveloper")
    assert user.fullname == "Joe Developer"
    assert user.title == "Web Developer"
    assert user.organization == "Acme, Inc."
    assert user.location == "Springfield, USA"
    assert user.irc_nickname == "joedev"
    assert user.twitter_url == "http://twitter.com/joedev1999"
    assert user.github_url == "https://github.com/joedev1999"
    assert user.stackoverflow_url == ("http://stackoverflow.com/users/1/joedev1999")
    assert user.linkedin_url == "http://www.linkedin.com/in/joedev1999"
    assert user.mozillians_url == "http://mozillians.org/u/joedev/"
    assert user.date_joined == datetime(1999, 1, 1, 10, 40, 23)


def test_save_user_banned(django_user_model):
    """A banned user creates a self-banning UserBan instance."""
    data = {"username": "banned", "date_joined": datetime(2016, 12, 19), "banned": True}
    Storage().save_user(data)
    user = django_user_model.objects.get(username="banned")
    assert user.bans.count() == 1
    ban = user.bans.first()
    assert ban.by == user
    assert ban.reason == "Ban detected by scraper"
