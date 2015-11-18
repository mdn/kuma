from nose.plugins.attrib import attr
from pyquery import PyQuery as pq

from constance.test import override_config
from jingo.helpers import urlparams
import requests_mock
from waffle.models import Flag

from kuma.core.urlresolvers import reverse
from kuma.spam.akismet import Akismet
from kuma.spam.constants import SPAM_SUBMISSIONS_FLAG, SPAM_URL, VERIFY_URL
from kuma.users.tests import UserTestCase
from kuma.users.models import User
from kuma.wiki.models import RevisionAkismetSubmission


@override_config(AKISMET_KEY='admin')
@attr('spam')
class AdminTestCase(UserTestCase):
    fixtures = UserTestCase.fixtures + ['wiki/documents.json']

    def test_spam_submission_filled(self):
        admin = User.objects.get(username='admin')
        revision = admin.created_revisions.all()[0]
        url = urlparams(
            reverse('admin:wiki_revisionakismetsubmission_add'),
            revision=revision.id,
            type='ham',
        )
        self.client.login(username='admin', password='testpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        page = pq(response.content)
        revision_inputs = page.find('input#id_revision')
        self.assertEqual(len(revision_inputs), 1)
        self.assertEqual(revision_inputs[0].value, str(revision.id))

        type_inputs = page.find('input[name=type]')
        self.assertEqual(len(type_inputs), 2)

        for type_input in type_inputs:
            if type_input.value == 'spam':
                self.assertTrue(not type_input.checked)
            elif type_input.value == 'ham':
                self.assertTrue(type_input.checked)

    @requests_mock.mock()
    def test_spam_submission_submitted(self, mock_requests):
        admin = User.objects.get(username='admin')
        flag, created = Flag.objects.get_or_create(name=SPAM_SUBMISSIONS_FLAG)
        flag.users.add(admin)
        revision = admin.created_revisions.all()[0]
        url = reverse('admin:wiki_revisionakismetsubmission_add')

        mock_requests.post(VERIFY_URL, content='valid')
        mock_requests.post(SPAM_URL, content=Akismet.submission_success)

        revision = admin.created_revisions.all()[0]
        data = {
            'revision': revision.id,
            'type': 'spam',
        }
        self.client.login(username='admin', password='testpass')
        url = reverse('admin:wiki_revisionakismetsubmission_add')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # successfully created the submission record
        submission = RevisionAkismetSubmission.objects.first()
        self.assertTrue(submission is not None)
        self.assertEqual(submission.sender, admin)
        self.assertTrue(submission.sent)
        self.assertEqual(submission.revision, revision)
        self.assertEqual(submission.type, 'spam')

        self.assertEqual(mock_requests.call_count, 2)
        request_body = mock_requests.request_history[1].body
        self.assertIn('user_ip=0.0.0.0', request_body)
        self.assertIn('user_agent=', request_body)
        self.assertIn(revision.slug, request_body)
