from django.core import mail
from django import test

from nose.tools import eq_

from notifications.tasks import send_notification
from notifications.models import EventWatch


class SendNotificationTestCase(test.TestCase):

    fixtures = ['notifications.json']

    def test_send_notification(self):
        """Check that email gets sent."""
        e = EventWatch.objects.all()[0]
        send_notification(e.content_type, e.watch_id,
                          'My Subject', 'My Content')

        eq_(2, len(mail.outbox))
        assert mail.outbox[0].subject == 'My Subject'
        assert mail.outbox[0].body == 'My Content'

    def test_exclude_notification(self):
        """Check that mail is not sent to the exclude list."""
        e = EventWatch.objects.all()[0]
        send_notification(e.content_type, e.watch_id,
                          'My Subject', 'My Content',
                          (e.email,))

        eq_(1, len(mail.outbox))
