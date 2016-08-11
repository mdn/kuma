import datetime
import json

from constance.test import override_config
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.http import parse_http_date_safe

from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import WikiTestCase, document, revision

from ..models import Attachment, AttachmentRevision
from . import make_test_file


@override_config(WIKI_ATTACHMENT_ALLOWED_TYPES='text/plain')
class AttachmentViewTests(UserTestCase, WikiTestCase):

    def setUp(self):
        super(AttachmentViewTests, self).setUp()
        self.client.login(username='admin', password='testpass')
        self.revision = revision(save=True)
        self.document = self.revision.document
        self.files_url = reverse('attachments.edit_attachment',
                                 kwargs={'document_path': self.document.slug},
                                 locale='en-US')

    @transaction.atomic
    def _post_attachment(self):
        file_for_upload = make_test_file(
            content='A test file uploaded into kuma.')
        post_data = {
            'title': 'Test uploaded file',
            'description': 'A test file uploaded into kuma.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }
        response = self.client.post(self.files_url,
                                    data=post_data)
        return response

    def test_legacy_redirect(self):
        test_user = self.user_model.objects.get(username='testuser2')
        test_file_content = 'Meh meh I am a test file.'
        test_files = (
            {'file_id': 97, 'filename': 'Canvas_rect.png',
             'title': 'Canvas rect'},
            {'file_id': 107, 'filename': 'Canvas_smiley.png',
             'title': 'Canvas smiley'},
            {'file_id': 86, 'filename': 'Canvas_lineTo.png',
             'title': 'Canvas lineTo'},
            {'file_id': 55, 'filename': 'Canvas_arc.png',
             'title': 'Canvas arc'},
        )
        for test_file in test_files:
            attachment = Attachment(
                title=test_file['title'],
                mindtouch_attachment_id=test_file['file_id'],
            )
            attachment.save()
            now = datetime.datetime.now()
            revision = AttachmentRevision(
                attachment=attachment,
                mime_type='text/plain',
                title=test_file['title'],
                description='',
                created=now,
                is_approved=True)
            revision.creator = test_user
            revision.file.save(test_file['filename'],
                               ContentFile(test_file_content))
            revision.make_current()
            mindtouch_url = reverse('attachments.mindtouch_file_redirect',
                                    args=(),
                                    kwargs={'file_id': test_file['file_id'],
                                            'filename': test_file['filename']})
            response = self.client.get(mindtouch_url)
            self.assertRedirects(response, attachment.get_file_url(),
                                 status_code=301,
                                 fetch_redirect_response=False)

    def test_get_request(self):
        response = self.client.get(self.files_url, follow=True)
        self.assertRedirects(response, self.document.get_edit_url())

    def test_edit_attachment(self):
        response = self._post_attachment()
        self.assertRedirects(response, self.document.get_edit_url())

        attachment = Attachment.objects.get(title='Test uploaded file')
        rev = attachment.current_revision
        self.assertEqual(rev.creator.username, 'admin')
        self.assertEqual(rev.description, 'A test file uploaded into kuma.')
        self.assertEqual(rev.comment, 'Initial upload')
        self.assertTrue(rev.is_approved)

    def test_attachment_raw_requires_attachment_host(self):
        response = self._post_attachment()
        attachment = Attachment.objects.get(title='Test uploaded file')

        url = attachment.get_file_url()
        response = self.client.get(url)
        self.assertRedirects(response, url,
                             fetch_redirect_response=False,
                             status_code=301)

        response = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        self.assertTrue(response.streaming)
        self.assertEqual(response['x-frame-options'],
                         'ALLOW-FROM %s' % settings.DOMAIN)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Last-Modified', response)
        self.assertNotIn('1970', response['Last-Modified'])
        self.assertIn('GMT', response['Last-Modified'])
        self.assertIsNotNone(parse_http_date_safe(response['Last-Modified']))

    def test_get_previous(self):
        """
        AttachmentRevision.get_previous() should return this revisions's
        files's most recent approved revision."""
        test_user = self.user_model.objects.get(username='testuser2')
        attachment = Attachment(title='Test attachment for get_previous')
        attachment.save()
        revision1 = AttachmentRevision(
            attachment=attachment,
            mime_type='text/plain',
            title=attachment.title,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        revision1.file.save('get_previous_test_file.txt',
                            ContentFile('I am a test file for get_previous'))
        revision1.save()
        revision1.make_current()

        revision2 = AttachmentRevision(
            attachment=attachment,
            mime_type='text/plain',
            title=attachment.title,
            description='',
            comment='First edit..',
            created=datetime.datetime.now(),
            creator=test_user,
            is_approved=True)
        revision2.file.save('get_previous_test_file.txt',
                            ContentFile('I am a test file for get_previous'))
        revision2.save()
        revision2.make_current()

        self.assertEqual(revision1, revision2.get_previous())

    @override_config(WIKI_ATTACHMENT_ALLOWED_TYPES='application/x-super-weird')
    def test_mime_type_filtering(self):
        """
        Don't allow uploads outside of the explicitly-permitted
        mime-types.
        """
        _file = make_test_file(content='plain and text', suffix='.txt')
        post_data = {
            'title': 'Test disallowed file type',
            'description': 'A file kuma should disallow on type.',
            'comment': 'Initial upload',
            'file': _file,
        }
        response = self.client.post(self.files_url, data=post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Files of this type are not permitted.')
        _file.close()

    def test_intermediate(self):
        """
        Test that the intermediate DocumentAttachment gets created
        correctly when adding an Attachment with a document_id.

        """
        doc = document(locale='en-US',
                       slug='attachment-test-intermediate',
                       save=True)
        revision(document=doc, is_approved=True, save=True)

        file_for_upload = make_test_file(
            content='A file for testing intermediate attachment model.')

        post_data = {
            'title': 'Intermediate test file',
            'description': 'Intermediate test file',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }
        files_url = reverse('attachments.edit_attachment',
                            kwargs={'document_path': doc.slug},
                            locale='en-US')
        response = self.client.post(files_url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(doc.files.count(), 1)
        intermediates = DocumentAttachment.objects.filter(document__pk=doc.id)
        self.assertEqual(intermediates.count(), 1)

        intermediate = intermediates[0]
        self.assertEqual(intermediate.attached_by.username, 'admin')
        self.assertEqual(intermediate.name,
                         file_for_upload.name.split('/')[-1])

    def test_feed(self):
        test_user = self.user_model.objects.get(username='testuser2')
        attachment = Attachment(title='Test attachment for get_previous')
        attachment.save()
        revision = AttachmentRevision(
            attachment=attachment,
            mime_type='text/plain',
            title=attachment.title,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        revision.file.save('get_previous_test_file.txt',
                           ContentFile('I am a test file for get_previous'))
        revision.save()
        revision.make_current()

        feed_url = reverse('attachments.feeds.recent_files', locale='en-US',
                           args=(), kwargs={'format': 'json'})
        response = self.client.get(feed_url)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], revision.title)
        self.assertEqual(data[0]['link'], revision.attachment.get_file_url())
        self.assertEqual(data[0]['author_name'], test_user.username)
