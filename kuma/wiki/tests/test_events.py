# -*- coding: utf-8 -*-
"""Tests for kuma.wiki.events."""
from __future__ import unicode_literals
from datetime import datetime

import mock
import pytest

from ..events import (EditDocumentEvent, first_edit_email,
                      notification_context)
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


def test_notification_context_for_create(create_revision):
    """Test the notification context for a created English page."""
    context = notification_context(create_revision)
    utm_campaign = ('?utm_campaign=Wiki+Doc+Edits&utm_medium=email'
                    '&utm_source=developer.mozilla.org')
    url = '/en-US/docs/Root'
    expected = {
        'compare_url': utm_campaign,
        'creator': create_revision.creator,
        'diff': 'Diff is unavailable.',
        'document_title': 'Root Document',
        'edit_url': url + '$edit' + utm_campaign,
        'history_url': url + '$history' + utm_campaign,
        'user_url': '/profiles/wiki_user' + utm_campaign,
        'view_url': url + utm_campaign
    }
    assert context == expected


def test_notification_context_for_edit(create_revision, edit_revision):
    """Test the notification context for an edited English page."""
    context = notification_context(edit_revision)
    utm_campaign = ('?utm_campaign=Wiki+Doc+Edits&utm_medium=email'
                    '&utm_source=developer.mozilla.org')
    url = '/en-US/docs/Root'
    compare_url = (url +
                   "$compare?to=%d" % edit_revision.id +
                   "&from=%d" % create_revision.id +
                   utm_campaign.replace("?", "&"))
    diff = """\
--- [en-US] #%d

+++ [en-US] #%d

@@ -5,7 +5,7 @@

   </head>
   <body>
     <p>
-      Getting started...
+      The root document.
     </p>
   </body>
 </html>""" % (create_revision.id, edit_revision.id)
    expected = {
        'compare_url': compare_url,
        'creator': edit_revision.creator,
        'diff': diff,
        'document_title': 'Root Document',
        'edit_url': url + '$edit' + utm_campaign,
        'history_url': url + '$history' + utm_campaign,
        'user_url': '/profiles/wiki_user' + utm_campaign,
        'view_url': url + utm_campaign
    }
    assert context == expected


@mock.patch('tidings.events.EventUnion.fire')
def test_edit_document_event_fires_union(mock_fire, create_revision,
                                         wiki_user):
    """Test that EditDocumentEvent also notifies for the tree."""
    EditDocumentEvent.notify(wiki_user, create_revision.document)
    EditDocumentEvent(create_revision).fire()
    mock_fire.assert_called_once_with()


@mock.patch('kuma.wiki.events.emails_with_users_and_watches')
def test_edit_document_event_emails_on_create(mock_emails, create_revision):
    """Test event email parameters for creation of an English page."""
    users_and_watches = [('fake_user', [None])]
    EditDocumentEvent(create_revision)._mails(users_and_watches)
    assert mock_emails.call_count == 1
    args, kwargs = mock_emails.call_args
    assert not args
    assert kwargs == {
        'subject': mock.ANY,
        'text_template': 'wiki/email/edited.ltxt',
        'html_template': None,
        'context_vars': notification_context(create_revision),
        'users_and_watches': users_and_watches,
        'default_locale': 'en-US'
    }
    subject = kwargs['subject'] % kwargs['context_vars']
    expected = '[MDN] Page "Root Document" changed by wiki_user'
    assert subject == expected


def test_first_edit_email_on_change(edit_revision):
    """A first edit email is formatted for an English change."""
    mail = first_edit_email(edit_revision)
    assert mail.subject == ('[MDN] [en-US] wiki_user made their first edit,'
                            ' to: Root Document')
    assert mail.extra_headers == {
        'X-Kuma-Document-Url': u'https://example.com/en-US/docs/Root',
        'X-Kuma-Editor-Username': u'wiki_user'
    }
