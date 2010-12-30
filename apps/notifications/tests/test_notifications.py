from django.core import mail
from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from notifications.tasks import (send_notification, delete_watches,
                                 update_email_in_notifications)
from notifications.models import EventWatch
from forums.models import Thread
from sumo.tests import TestCase


class SendNotificationTestCase(TestCase):
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

    def test_from_address(self):
        """Check that mails come from the right address."""
        e = EventWatch.objects.all()[0]
        send_notification(e.content_type, e.watch_id,
                          'My Subject', 'My Content')
        eq_(mail.outbox[0].from_email, 'notifications@support.mozilla.com')


class DeleteNotificationsTestCase(TestCase):
    fixtures = ['notifications.json']

    def test_delete_task(self):
        eq_(0, EventWatch.uncached.filter(watch_id=2).count())
        ct = ContentType.objects.get_for_model(Thread)
        EventWatch.objects.create(content_type=ct, watch_id=2,
                                  email='me@x.org')
        EventWatch.objects.create(content_type=ct, watch_id=2,
                                  email='you@x.org')
        eq_(2, EventWatch.uncached.filter(watch_id=2).count())
        delete_watches(Thread, 2)
        eq_(0, EventWatch.uncached.filter(watch_id=2).count())


class UpdateEmailInNotificationsTestCase(TestCase):
    fixtures = ['notifications.json']

    def test_update_email(self):
        update_email_in_notifications(old='noone2@example.com',
                                      new='user2@nowhere.com')
        ew = EventWatch.uncached.get(pk=2)
        eq_('user2@nowhere.com', ew.email)
