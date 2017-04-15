# -*- coding: utf-8 -*-
"""py.test fixtures for kuma.wiki.tests."""

import pytest
from datetime import datetime

from ..models import Document, Revision


class Object(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def wiki_user(db, django_user_model):
    """A test user."""
    return django_user_model.objects.create(
        username='wiki_user',
        email='wiki_user@example.com',
        date_joined=datetime(2017, 4, 14, 12, 0))


@pytest.fixture
def wiki_user_2(db, django_user_model):
    """A second test user."""
    return django_user_model.objects.create(
        username='wiki_user_2',
        email='wiki_user_2@example.com',
        date_joined=datetime(2017, 4, 17, 10, 30))


@pytest.fixture
def wiki_user_3(db, django_user_model):
    """A third test user."""
    return django_user_model.objects.create(
        username='wiki_user_3',
        email='wiki_user_3@example.com',
        date_joined=datetime(2017, 4, 23, 11, 45))


@pytest.fixture
def inactive_wiki_user(db, django_user_model):
    """An inactive test user."""
    return django_user_model.objects.create(
        is_active=False,
        username='wiki_user_slacker',
        email='wiki_user_slacker@example.com',
        date_joined=datetime(2017, 4, 19, 10, 58))


@pytest.fixture
def banned_wiki_user(db, django_user_model, wiki_user):
    """A banned test user."""
    user = django_user_model.objects.create(
        username='bad_wiki_user',
        email='bad_wiki_user@example.com',
        date_joined=datetime(2017, 4, 18, 9, 15)
    )
    ban = user.bans.create(by=wiki_user, reason='because')
    return Object(
        user=user,
        ban=ban
    )


@pytest.fixture
def root_doc(wiki_user):
    """A newly-created top-level English document."""
    root_doc = Document.objects.create(
        locale='en-US', slug='Root', title='Root Document')
    Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content='<p>Getting started...</p>',
        title='Root Document',
        created=datetime(2017, 4, 14, 12, 15))
    return root_doc


@pytest.fixture
def create_revision(root_doc):
    """A revision that created an English document."""
    return root_doc.revisions.first()


@pytest.fixture
def edit_revision(root_doc, wiki_user):
    """A revision that edits an English document."""
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user,
        content='<p>The root document.</p>',
        comment='Done with initial version.',
        created=datetime(2017, 4, 14, 12, 30))
    root_doc.save()
    return root_doc.current_revision


@pytest.fixture
def trans_doc(create_revision, wiki_user):
    """Translate the root document into French."""
    trans_doc = Document.objects.create(
        locale='fr',
        parent=create_revision.document,
        slug='Racine',
        title='Racine du Document')
    Revision.objects.create(
        document=trans_doc,
        creator=wiki_user,
        based_on=create_revision,
        content='<p>Mise en route...</p>',
        title='Racine du Document',
        created=datetime(2017, 4, 14, 12, 20))
    return trans_doc


@pytest.fixture
def trans_revision(trans_doc):
    return trans_doc.current_revision


@pytest.fixture
def multi_generational_docs(wiki_user):
    great_grandparent_doc = Document.objects.create(
        locale='en-US',
        slug='Great-grandparent',
        title='Great-grandparent Document'
    )
    Revision.objects.create(
        document=great_grandparent_doc,
        creator=wiki_user,
        content='<p>Great-grandparent...</p>',
        title='Great-grandparent Document',
        created=datetime(2017, 4, 24, 13, 49)
    )

    grandparent_doc = Document.objects.create(
        locale='en-US',
        slug='Grandparent',
        title='Grandparent Document',
        parent_topic=great_grandparent_doc
    )
    Revision.objects.create(
        document=grandparent_doc,
        creator=wiki_user,
        content='<p>Grandparent...</p>',
        title='Grandparent Document',
        created=datetime(2017, 4, 24, 13, 50)
    )

    parent_doc = Document.objects.create(
        locale='en-US',
        slug='Parent',
        title='Parent Document',
        parent_topic=grandparent_doc
    )
    Revision.objects.create(
        document=parent_doc,
        creator=wiki_user,
        content='<p>Parent...</p>',
        title='Parent Document',
        created=datetime(2017, 4, 24, 13, 51)
    )

    child_doc = Document.objects.create(
        locale='en-US',
        slug='Child',
        title='Child Document',
        parent_topic=parent_doc
    )
    Revision.objects.create(
        document=child_doc,
        creator=wiki_user,
        content='<p>Child...</p>',
        title='Child Document',
        created=datetime(2017, 4, 24, 13, 52)
    )

    return Object(
        child=child_doc,
        parent=parent_doc,
        grandparent=grandparent_doc,
        great_grandparent=great_grandparent_doc
    )


@pytest.fixture
def root_doc_with_mixed_contributors(root_doc, wiki_user, wiki_user_2,
                                     inactive_wiki_user, banned_wiki_user):
    """
    A top-level English document with mixed contributors (some are valid,
    some are banned, and some are inactive).
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=wiki_user_2,
        content='<p>The root document.</p>',
        comment='Done with the initial version.',
        created=datetime(2017, 4, 17, 12, 35))
    root_doc.save()

    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=inactive_wiki_user,
        content='<p>The root document re-envisioned.</p>',
        comment='Done with the second revision.',
        created=datetime(2017, 4, 18, 10, 15))
    root_doc.save()

    root_doc.current_revision = Revision.objects.create(
        document=root_doc,
        creator=banned_wiki_user.user,
        content='<p>The root document re-envisioned with malice.</p>',
        comment='Nuke the previous revision.',
        created=datetime(2017, 4, 19, 10, 15))
    root_doc.save()

    return Object(
        doc=root_doc,
        valid_contributors=[wiki_user_2, wiki_user],
        banned_contributor=banned_wiki_user,
        inactive_contributor=inactive_wiki_user
    )
