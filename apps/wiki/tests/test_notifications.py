from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from . import TestCaseBase, revision
import notifications.tasks
from wiki.tasks import (send_reviewed_notification,
                        send_ready_for_review_notification,
                        send_edited_notification)


REVIEWED_EMAIL_CONTENT = """

Your revision has been reviewed.

admin has approved your revision to the document
%s.

Message from the reviewer:

%s

To view the history of this document, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/history
"""

READY_FOR_REVIEW_EMAIL_CONTENT = """


jsocol submitted a new revision to the document
%s.

To review this revision, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/review/%s
"""

DOCUMENT_EDITED_EMAIL_CONTENT = """


jsocol created a new revision to the document
%s.

To view this document's history, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/history
"""


class NotificationTestCase(TestCaseBase):
    """Test that notifications get sent."""
    fixtures = ['users.json']

    def _approve_and_send(self, revision, reviewer, message):
        revision.reviewer = reviewer
        revision.reviewed = datetime.now()
        revision.is_approved = True
        revision.save()
        send_reviewed_notification(revision, revision.document, message)

    @mock.patch_object(Site.objects, 'get_current')
    def test_reviewed_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        doc = rev.document
        msg = "great work!"
        self._approve_and_send(rev, User.objects.get(username='admin'), msg)

        eq_(1, len(mail.outbox))
        eq_('Your revision has been approved: %s' % doc.title,
            mail.outbox[0].subject)
        eq_([rev.creator.email], mail.outbox[0].to)
        eq_(REVIEWED_EMAIL_CONTENT % (doc.title, msg, doc.slug),
            mail.outbox[0].body)

    @mock.patch_object(Site.objects, 'get_current')
    def test_reviewed_by_creator_no_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        msg = "great work!"
        self._approve_and_send(rev, rev.creator, msg)

        # Verify no email was sent
        eq_(0, len(mail.outbox))

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_ready_for_review_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        rev.save()
        doc = rev.document
        send_ready_for_review_notification(rev, doc)
        delay.assert_called_with(
            ContentType.objects.get_for_model(doc), None,
            u'%s is ready for review (%s)' % (doc.title, rev.creator),
            READY_FOR_REVIEW_EMAIL_CONTENT % (doc.title, doc.slug, rev.id),
            (u'user118533@nowhere',),
            'ready_for_review', 'en-US')

    @mock.patch_object(notifications.tasks.send_notification, 'delay')
    @mock.patch_object(Site.objects, 'get_current')
    def test_document_edited_notification(self, get_current, delay):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        rev.save()
        doc = rev.document
        send_edited_notification(rev, doc)
        delay.assert_called_with(
            ContentType.objects.get_for_model(doc), doc.id,
            u'%s was edited by %s' % (doc.title, rev.creator),
            DOCUMENT_EDITED_EMAIL_CONTENT % (doc.title, doc.slug),
            (u'user118533@nowhere',),
            'edited', '')
