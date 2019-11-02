# -*- coding: utf-8 -*-
"""py.test fixtures"""


from datetime import datetime

import pytest

from kuma.wiki.models import Document, Revision


@pytest.fixture
def simple_user(db, django_user_model):
    """A simple User record with only the basic information."""
    return django_user_model.objects.create(
        username='JackDeveloper',
        email='jack@example.com',
        date_joined=datetime(2016, 11, 4, 9, 1))


@pytest.fixture
def simple_doc(db):
    """A Document record with no revisions and no parent topic."""
    return Document.objects.create(
        locale='en-US', slug='Root', title='Root Document')


@pytest.fixture
def root_doc(simple_doc, simple_user):
    """A Document record with two revisions and without a parent topic."""
    Revision.objects.create(
        document=simple_doc,
        creator=simple_user,
        content='<p>Getting started...</p>',
        title='Root Document',
        created=datetime(2016, 1, 1))
    current_rev = Revision.objects.create(
        document=simple_doc,
        creator=simple_user,
        content='<p>The root document.</p>',
        created=datetime(2016, 2, 1))
    assert simple_doc.current_revision == current_rev
    return simple_doc


@pytest.fixture
def translated_doc(root_doc):
    """A translation of the root document."""
    translated_doc = Document.objects.create(
        parent=root_doc,
        slug='Racine',
        locale='fr',
        title='Document Racine')
    current_rev = Revision.objects.create(
        document=translated_doc,
        content='<p>Commencer...</p>',
        title='Document Racine',
        slug='Racine',
        based_on=root_doc.current_revision,
        creator=root_doc.current_revision.creator,
        created=datetime(2017, 6, 1, 15, 28))
    assert translated_doc.current_revision == current_rev
    return translated_doc
