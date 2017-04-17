# -*- coding: utf-8 -*-
"""py.test fixtures for kuma.wiki.tests."""

import pytest
from datetime import datetime

from ..models import Document, Revision


@pytest.fixture
def wiki_user(db, django_user_model):
    """A test user."""
    return django_user_model.objects.create(
        username='wiki_user',
        email='wiki_user@example.com',
        date_joined=datetime(2017, 4, 14, 12, 0))


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
