"""Tests for kuma.wiki.events."""


from datetime import datetime
from unittest import mock

from django.urls import reverse

from kuma.core.utils import order_params

from ..events import (EditDocumentEvent, first_edit_email,
                      notification_context, spam_attempt_email)
from ..models import DocumentSpamAttempt


def test_notification_context_for_create(create_revision):
    """Test the notification context for a created English page."""
    context = notification_context(create_revision)
    utm_campaign = ('?utm_campaign=Wiki+Doc+Edits&utm_medium=email'
                    '&utm_source=developer.mozilla.org')
    url = '/en-US/docs/Root'
    user_url = reverse('users.user_detail', kwargs={'username': 'wiki_user'})
    expected = {
        'compare_url': '',
        'creator': create_revision.creator,
        'diff': 'Diff is unavailable.',
        'document_title': 'Root Document',
        'locale': 'en-US'
    }

    expected_urls = {
        'edit_url': order_params(url + '$edit' + utm_campaign),
        'history_url': order_params(url + '$history' + utm_campaign),
        'user_url': order_params(user_url + utm_campaign),
        'view_url': order_params(url + utm_campaign)
    }

    assert_expectations_url(context, expected, expected_urls)


def test_notification_context_for_edit(create_revision, edit_revision):
    """Test the notification context for an edited English page."""
    context = notification_context(edit_revision)
    utm_campaign = ('?utm_campaign=Wiki+Doc+Edits&utm_medium=email'
                    '&utm_source=developer.mozilla.org')
    url = '/en-US/docs/Root'
    user_url = reverse('users.user_detail', kwargs={'username': 'wiki_user'})
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
        'creator': edit_revision.creator,
        'diff': diff,
        'document_title': 'Root Document',
        'locale': 'en-US'
    }

    expected_urls = {
        'compare_url': order_params(compare_url),
        'edit_url': order_params(url + '$edit' + utm_campaign),
        'history_url': order_params(url + '$history' + utm_campaign),
        'user_url': order_params(user_url + utm_campaign),
        'view_url': url + utm_campaign
    }

    assert_expectations_url(context, expected, expected_urls)


def test_notification_context_for_translation(trans_revision, create_revision):
    """Test the notification context for a created English page."""
    context = notification_context(trans_revision)
    utm_campaign = ('?utm_campaign=Wiki+Doc+Edits&utm_medium=email'
                    '&utm_source=developer.mozilla.org')
    url = '/fr/docs/Racine'
    user_url = reverse('users.user_detail', kwargs={'username': 'wiki_user'})
    compare_url = (url +
                   "$compare?to=%d" % trans_revision.id +
                   "&from=%d" % create_revision.id +
                   utm_campaign.replace("?", "&"))
    diff = """\
--- [en-US] #%d

+++ [fr] #%d

@@ -5,7 +5,7 @@

   </head>
   <body>
     <p>
-      Getting started...
+      Mise en route...
     </p>
   </body>
 </html>""" % (create_revision.id, trans_revision.id)
    expected = {
        'creator': trans_revision.creator,
        'diff': diff,
        'document_title': 'Racine du Document',
        'locale': 'fr'
    }

    expected_urls = {
        'compare_url': order_params(compare_url),
        'edit_url': order_params(url + '$edit' + utm_campaign),
        'history_url': order_params(url + '$history' + utm_campaign),
        'user_url': order_params(user_url + utm_campaign),
        'view_url': order_params(url + utm_campaign)
    }

    assert_expectations_url(context, expected, expected_urls)


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
        'default_locale': 'en-US',
        'headers': {
            'X-Kuma-Editor-Username': 'wiki_user',
            'X-Kuma-Document-Url': create_revision.document.get_full_url(),
            'X-Kuma-Document-Title': 'Root Document',
            'X-Kuma-Document-Locale': 'en-US',
        }
    }
    subject = kwargs['subject'] % kwargs['context_vars']
    expected = '[MDN][en-US][New] Page "Root Document" created by wiki_user'
    assert subject == expected


@mock.patch('kuma.wiki.events.emails_with_users_and_watches')
def test_edit_document_event_emails_on_change(mock_emails, edit_revision):
    """Test event email parameters for changing an English page."""
    users_and_watches = [('fake_user', [None])]
    EditDocumentEvent(edit_revision)._mails(users_and_watches)
    assert mock_emails.call_count == 1
    args, kwargs = mock_emails.call_args
    assert not args
    context = notification_context(edit_revision)
    assert kwargs['context_vars'] == context
    subject = kwargs['subject'] % context
    expected = '[MDN][en-US] Page "Root Document" changed by wiki_user'
    assert subject == expected


def test_first_edit_email_on_create(create_revision):
    """A first edit email is formatted for a new English page."""
    mail = first_edit_email(create_revision)
    assert mail.subject == ('[MDN][en-US][New] wiki_user made their first edit,'
                            ' creating: Root Document')
    assert mail.extra_headers == {
        'X-Kuma-Editor-Username': 'wiki_user',
        'X-Kuma-Document-Url': create_revision.document.get_full_url(),
        'X-Kuma-Document-Title': 'Root Document',
        'X-Kuma-Document-Locale': 'en-US',
    }


def test_first_edit_email_on_change(edit_revision):
    """A first edit email is formatted for an English change."""
    mail = first_edit_email(edit_revision)
    assert mail.subject == ('[MDN][en-US] wiki_user made their first edit,'
                            ' to: Root Document')


def test_first_edit_email_on_translate(trans_revision):
    """A first edit email is formatted for a first translation."""
    mail = first_edit_email(trans_revision)
    assert mail.subject == ('[MDN][fr][New] wiki_user made their first edit,'
                            ' creating: Racine du Document')
    assert mail.extra_headers == {
        'X-Kuma-Editor-Username': 'wiki_user',
        'X-Kuma-Document-Url': trans_revision.document.get_full_url(),
        'X-Kuma-Document-Title': 'Racine du Document',
        'X-Kuma-Document-Locale': 'fr',
    }


def test_spam_attempt_email_on_create(wiki_user):
    """A spam attempt email is formatted for a new English page."""
    spam_attempt = DocumentSpamAttempt(
        user=wiki_user,
        title='My new spam page',
        slug='my-new-spam-page',
        created=datetime(2017, 4, 14, 15, 13)
    )
    mail = spam_attempt_email(spam_attempt)
    assert mail.subject == ('[MDN] Wiki spam attempt recorded with title'
                            ' My new spam page')
    assert mail.extra_headers == {
        'X-Kuma-Editor-Username': 'wiki_user'
    }


def test_spam_attempt_email_on_change(wiki_user, root_doc):
    """A spam attempt email is formatted for an English change."""
    spam_attempt = DocumentSpamAttempt(
        user=wiki_user,
        title='A spam revision',
        slug=root_doc.slug,
        document=root_doc,
        created=datetime(2017, 4, 14, 15, 14)
    )
    mail = spam_attempt_email(spam_attempt)
    assert mail.subject == ('[MDN] Wiki spam attempt recorded for document'
                            ' /en-US/docs/Root (Root Document)')
    assert mail.extra_headers == {
        'X-Kuma-Editor-Username': 'wiki_user',
        'X-Kuma-Document-Url': root_doc.get_full_url(),
        'X-Kuma-Document-Title': 'Root Document',
        'X-Kuma-Document-Locale': 'en-US',
    }


def test_spam_attempt_email_on_translate(wiki_user, trans_doc):
    """A spam attempt email is formatted for a new translation."""
    spam_attempt = DocumentSpamAttempt(
        user=wiki_user,
        title='Ma nouvelle page de spam',
        slug='ma-nouvelle-page-de-spam',
        created=datetime(2017, 4, 15, 10, 54)
    )
    mail = spam_attempt_email(spam_attempt)
    assert mail.subject == ('[MDN] Wiki spam attempt recorded with title'
                            ' Ma nouvelle page de spam')


def test_spam_attempt_email_partial_model(wiki_user):
    """A spam attempt email is formatted with partial information."""
    spam_attempt = DocumentSpamAttempt(
        user=wiki_user,
        slug='my-new-spam-page',
        created=datetime(2017, 4, 14, 15, 13)
    )
    mail = spam_attempt_email(spam_attempt)
    assert mail.subject == ('[MDN] Wiki spam attempt recorded')
    assert mail.extra_headers == {
        'X-Kuma-Editor-Username': 'wiki_user',
    }


def assert_expectations_url(context, expected, expected_urls):
    for key in expected.keys():
        assert context[key] == expected[key]
    for key in expected_urls.keys():
        assert order_params(context[key]) == expected_urls[key]
