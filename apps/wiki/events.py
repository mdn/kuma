# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import Context, loader

from tower import ugettext as _

from devmo import email_utils
from tidings.events import InstanceEvent, Event
from sumo.urlresolvers import reverse
from wiki.helpers import revisions_unified_diff
from wiki.models import Document


log = logging.getLogger('mdn.wiki.events')


def context_dict(revision):
    """Return a dict that fills in the blanks in notification templates."""
    document = revision.document
    from_revision = revision.get_previous()
    to_revision = revision
    diff = revisions_unified_diff(from_revision, to_revision)

    compare_url = ''
    if from_revision:
        compare_url = (reverse('wiki.compare_revisions',
            args=[document.full_path], locale=document.locale)
            + '?from=%s&to=%s' % (from_revision.id, to_revision.id))

    return {
        'document_title': document.title,
        'creator': revision.creator,
        'host': Site.objects.get_current().domain,
        'compare_url': compare_url,
        'view_url': reverse('wiki.document',
                            locale=document.locale,
                            args=[document.slug]),
        'edit_url': reverse('wiki.edit_document',
                            locale=document.locale,
                            args=[document.slug]),
        'history_url': reverse('wiki.document_revisions',
                               locale=document.locale,
                               args=[document.slug]),

        'diff': diff
    }

def notification_mails(revision, subject, template, url, users_and_watches):
    """Return EmailMessages in standard notification mail format."""
    document = revision.document
    subject = subject.format(title=document.title, creator=revision.creator,
                             locale=document.locale)
    t = loader.get_template(template)
    c = {'document_title': document.title,
         'creator': revision.creator,
         'url': url,
         'host': Site.objects.get_current().domain}
    content = t.render(Context(c))
    mail = EmailMessage(subject, content, settings.TIDINGS_FROM_ADDRESS)

    for u, dummy in users_and_watches:
        mail.to = [u.email]
        yield mail


class EditDocumentEvent(InstanceEvent):
    """Event fired when a certain document is edited"""
    event_type = 'wiki edit document'
    content_type = Document

    def __init__(self, revision):
        super(EditDocumentEvent, self).__init__(revision.document)
        self.revision = revision

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug('Sending edited notification email for document (id=%s)' %
                   document.id)
        subject = _('[MDN] Page "{document_title}" changed by {creator}')
        context = context_dict(revision)

        return email_utils.emails_with_users_and_watches(
            subject=subject,
            text_template='wiki/email/edited.ltxt',
            html_template=None,
            context_vars=context,
            users_and_watches=users_and_watches,
            default_locale=document.locale)


class _RevisionInLocaleEvent(Event):
    """An event that receives a revision when constructed and filters according
    to that revision's document's locale"""
    filters = set(['locale'])

    def __init__(self, revision):
        super(_RevisionInLocaleEvent, self).__init__()
        self.revision = revision

    # notify(), stop_notifying(), and is_notifying() take...
    # (user_or_email, locale=some_locale)

    def _users_watching(self, **kwargs):
        return self._users_watching_by_filter(
            locale=self.revision.document.locale, **kwargs)


class ReviewableRevisionInLocaleEvent(_RevisionInLocaleEvent):
    """Event fired when any revision in a certain locale is ready for review"""
    # No other content types have a concept of reviewability, so we don't
    # bother setting content_type.
    event_type = 'reviewable wiki in locale'

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        # log.debug('Sending ready for review email for revision (id=%s)' %
        #           revision.id)
        subject = _('{title} is ready for review ({creator})')
        url = reverse('wiki.review_revision', locale=document.locale,
                      args=[document.slug, revision.id])
        return notification_mails(revision, subject,
                                  'wiki/email/ready_for_review.ltxt', url,
                                  users_and_watches)


class ApproveRevisionInLocaleEvent(_RevisionInLocaleEvent):
    """Event fired when any revision in a certain locale is approved"""
    # No other content types have a concept of approval, so we don't bother
    # setting content_type.
    event_type = 'approved wiki in locale'

    def _mails(self, users_and_watches):
        revision = self.revision
        document = revision.document
        log.debug('Sending approved email for revision (id=%s)' %
                  revision.id)
        subject = _('{title} ({locale}) has a new approved revision')
        url = reverse('wiki.document', locale=document.locale,
                      args=[document.slug])
        return notification_mails(revision, subject,
                                  'wiki/email/approved.ltxt', url,
                                  users_and_watches)
