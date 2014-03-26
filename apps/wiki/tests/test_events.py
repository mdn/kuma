import constance.config
from nose.tools import eq_, ok_

from django.core import mail
from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
from wiki.tests import TestCaseBase, revision
from wiki.events import context_dict, EditDocumentEvent,\
        ReviewableRevisionInLocaleEvent, ApproveRevisionInLocaleEvent


class NotificationEmailTests(TestCaseBase):
    fixtures = ['test_users.json']

    def test_context_dict_no_previous_revision(self):
        rev = revision()
        try:
            cd = context_dict(rev)
        except AttributeError:
            self.fail("Should not throw AttributeError")
        eq_(cd, cd)


class PixelTrackingTests(TestCaseBase):
    '''
    Testsuite is dedicated for tests related to read-tracking pixel which is added
    to emails sent by wiki-events implementation.
    '''
    fixtures = ['test_users.json']

    def setUp(self):
        self.old_ga_account = constance.config.GOOGLE_ANALYTICS_ACCOUNT
        constance.config.GOOGLE_ANALYTICS_ACCOUNT = 'UA-TESTTEST-TE'
        self.rev = revision()
        self.rev.save()
        self.doc = self.rev.document
        self.locale = self.doc.locale
        self.testuser = User.objects.get(username='testuser')

    def tearDown(self):
        constance.config.GOOGLE_ANALYTICS_ACCOUNT = self.old_ga_account

    def check_tracking_pixel(self)
        ''' Checks if last sent mail contains read-tracking pixel, '''
        event_mail = mail.outbox[0]
        ok_(self.testuser.email in event_mail.to)
        ok_(reverse('track.mail.view', kwargs={'el': event_mail.subject})
            in event_mail.alternatives[0][0])

    def test_edit_document_event_tracking(self):
        EditDocumentEvent.notify(self.testuser, self.doc).activate().save()
        event_edit_document = EditDocumentEvent(self.rev)
        event_edit_document.fire()
        self.check_tracking_pixel()

    def test_reviewable_locale_revision_event_tracking(self):
        ReviewableRevisionInLocaleEvent.notify(self.testuser, locale=self.locale)\
                                       .activate().save()
        event_reviewable_revision = ReviewableRevisionInLocaleEvent(self.rev)
        event_reviewable_revision.fire()
        self.check_tracking_pixel()

    def test_approved_revision_event_tracking(self):
        ApproveRevisionInLocaleEvent.notify(self.testuser, locale=self.locale)\
                                    .activate().save()
        approved_revision = ApproveRevisionInLocaleEvent(self.rev)
        approved_revision.fire()
        self.check_tracking_pixel()
