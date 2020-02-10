"""Send notification emails for editing events."""


import logging

from constance import config
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from tidings.events import EventUnion, InstanceEvent

from kuma.core.email_utils import emails_with_users_and_watches
from kuma.core.templatetags.jinja_helpers import add_utm
from kuma.core.urlresolvers import reverse

from .models import Document
from .templatetags.jinja_helpers import get_compare_url, revisions_unified_diff


log = logging.getLogger("kuma.wiki.events")


def notification_context(revision):
    """
    Return a dict that fills in the blanks in notification templates.
    """
    document = revision.document
    # Don't use `previous` since it is cached. (see bug 1239141)
    from_revision = revision.get_previous()
    to_revision = revision
    diff = revisions_unified_diff(from_revision, to_revision)

    context = {
        "document_title": document.title,
        "creator": revision.creator,
        "diff": diff,
        "locale": document.locale,
    }

    if from_revision:
        compare_url = get_compare_url(document, from_revision.id, to_revision.id)
    else:
        compare_url = ""

    link_urls = {
        "user_url": revision.creator.get_absolute_url(),
        "compare_url": compare_url,
        "view_url": document.get_absolute_url(),
        "edit_url": document.get_edit_url(),
        "history_url": reverse(
            "wiki.document_revisions", locale=document.locale, args=[document.slug]
        ),
    }

    for name, url in link_urls.items():
        if url:
            context[name] = add_utm(url, "Wiki Doc Edits")
        else:
            context[name] = url

    return context


def extra_headers(user, document=None):
    """Get extra headers for filtering notification emails."""
    headers = {"X-Kuma-Editor-Username": user.username}
    if document:
        headers["X-Kuma-Document-Url"] = document.get_full_url()
        headers["X-Kuma-Document-Title"] = document.title
        headers["X-Kuma-Document-Locale"] = document.locale
    return headers


class EditDocumentEvent(InstanceEvent):
    """
    Event fired when a certain document is edited
    """

    event_type = "wiki edit document"
    content_type = Document

    def __init__(self, revision):
        super(EditDocumentEvent, self).__init__(revision.document)
        self.revision = revision

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug(
            "Sending edited notification email for document (id=%s)" % document.id
        )
        if document.revisions.only("id").first().id == revision.id:
            subject = _(
                '[MDN][%(locale)s][New] Page "%(document_title)s"'
                " created by %(creator)s"
            )
        else:
            subject = _(
                '[MDN][%(locale)s] Page "%(document_title)s"' " changed by %(creator)s"
            )
        context = notification_context(revision)

        return emails_with_users_and_watches(
            subject=subject,
            text_template="wiki/email/edited.ltxt",
            html_template=None,
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale,
            headers=extra_headers(revision.creator, document),
        )

    def fire(self, **kwargs):
        parent_events = [
            EditDocumentInTreeEvent(doc)
            for doc in self.revision.document.get_topic_parents()
        ]
        return EventUnion(
            self, EditDocumentInTreeEvent(self.revision.document), *parent_events
        ).fire(**kwargs)


class EditDocumentInTreeEvent(InstanceEvent):
    """
    Event class for subscribing to all document edits to and under a document

    Note: Do not call this class's .fire() method directly.
    """

    event_type = "wiki edit document in tree"
    content_type = Document


def first_edit_email(revision):
    """Create a notification email for first-time editors."""
    user, doc = revision.creator, revision.document
    if doc.revisions.only("id").first().id == revision.id:
        subject_tmpl = (
            "[MDN][%(loc)s][New] %(user)s made their first edit," " creating: %(doc)s"
        )
    else:
        subject_tmpl = "[MDN][%(loc)s] %(user)s made their first edit," " to: %(doc)s"
    subject = subject_tmpl % {
        "loc": doc.locale,
        "user": user.username,
        "doc": doc.title,
    }
    message = render_to_string("wiki/email/edited.ltxt", notification_context(revision))
    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        to=[config.EMAIL_LIST_SPAM_WATCH],
        headers=extra_headers(user, doc),
    )
    return email


def spam_attempt_email(spam_attempt):
    """
    Create a notification email for a spam attempt.

    Because the spam may be on document creation, the document might be null.
    """
    subject = "[MDN] Wiki spam attempt recorded"
    document = spam_attempt.document
    if document:
        subject = "%s for document %s" % (subject, document)
    elif spam_attempt.title:
        subject = "%s with title %s" % (subject, spam_attempt.title)
    body = render_to_string("wiki/email/spam.ltxt", {"spam_attempt": spam_attempt})
    email = EmailMessage(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        to=[config.EMAIL_LIST_SPAM_WATCH],
        headers=extra_headers(spam_attempt.user, document),
    )
    return email
