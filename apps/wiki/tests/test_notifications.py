from datetime import datetime

from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core import mail

import mock
from nose.tools import eq_

from wiki.tasks import send_reviewed_notification
from . import TestCaseBase, revision


EMAIL_CONTENT = (
    """

Your revision has been reviewed.

admin has approved your revision to the document 
%s.

Message from the reviewer:

%s

To view the history of this document, click the following
link, or paste it into your browser's location bar:

https://testserver/en-US/kb/%s/history
""",
)


class NotificationTestCase(TestCaseBase):
    """Test that notifications get sent."""
    fixtures = ['users.json']

    @mock.patch_object(Site.objects, 'get_current')
    def test_solution_notification(self, get_current):
        get_current.return_value.domain = 'testserver'

        rev = revision()
        doc = rev.document
        rev.reviewer = User.objects.get(username='admin')
        rev.reviewed = datetime.now()
        rev.is_approved = True
        rev.save()
        msg = "great work!"
        send_reviewed_notification(rev, doc, msg)

        eq_(1, len(mail.outbox))
        eq_('Your revision has been approved: %s' % doc.title,
            mail.outbox[0].subject)
        eq_([rev.creator.email], mail.outbox[0].to)
        eq_(EMAIL_CONTENT[0] % (doc.title, msg, doc.slug), mail.outbox[0].body)
