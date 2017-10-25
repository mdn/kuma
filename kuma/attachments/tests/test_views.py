import json
import datetime

import pytest
from pyquery import PyQuery as pq
from constance.test import override_config
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.six.moves.urllib.parse import urlparse

from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import WikiTestCase, document, revision
from kuma.attachments.utils import convert_to_http_date

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

    def test_edit_attachment(self):
        response = self._post_attachment()
        self.assertRedirects(response, self.document.get_edit_url())

        attachment = Attachment.objects.get(title='Test uploaded file')
        rev = attachment.current_revision
        self.assertEqual(rev.creator.username, 'admin')
        self.assertEqual(rev.description, 'A test file uploaded into kuma.')
        self.assertEqual(rev.comment, 'Initial upload')
        self.assertTrue(rev.is_approved)

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


def test_legacy_redirect(client, file_attachment):
    mindtouch_url = reverse(
        'attachments.mindtouch_file_redirect',
        args=(),
        kwargs={
            'file_id': file_attachment['file']['id'],
            'filename': file_attachment['file']['name']
        }
    )
    response = client.get(mindtouch_url)
    assert response.status_code == 301
    assert 'Location' in response
    assert response['Location'] == file_attachment['attachment'].get_file_url()
    assert not response.has_header('Vary')


def test_edit_attachment_get(admin_client, root_doc):
    url = reverse(
        'attachments.edit_attachment',
        kwargs={'document_path': root_doc.slug},
        locale='en-US'
    )
    response = admin_client.get(url)
    assert response.status_code == 302
    assert 'Location' in response
    assert urlparse(response['Location']).path == root_doc.get_edit_url()


@pytest.mark.parametrize('mode', ['empty-file', 'no-file'])
def test_edit_attachment_post_with_vacant_file(admin_client, root_doc, tmpdir,
                                               mode):
    post_data = {
        'title': 'Test uploaded file',
        'description': 'A test file uploaded into kuma.',
        'comment': 'Initial upload',
    }

    if mode == 'empty-file':
        empty_file = tmpdir.join('empty')
        empty_file.write('')
        post_data['file'] = empty_file
        expected = 'The submitted file is empty.'
    else:
        expected = 'This field is required.'

    url = reverse('attachments.edit_attachment',
                  kwargs={'document_path': root_doc.slug},
                  locale='en-US')
    response = admin_client.post(url, data=post_data)
    assert response.status_code == 200
    doc = pq(response.content)
    assert doc('ul.errorlist a[href="#id_file"]').html() == expected


def test_raw_file_requires_attachment_host(client, settings, file_attachment):
    settings.ATTACHMENT_HOST = 'demos'
    attachment = file_attachment['attachment']
    created = attachment.current_revision.created
    url = attachment.get_file_url()

    # Force the HOST header to look like something other than "demos".
    response = client.get(url, HTTP_HOST='localhost')
    assert response.status_code == 301
    assert response['Location'] == url
    assert 'Vary' not in response

    response = client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
    assert response.status_code == 200
    assert response.streaming
    assert response['x-frame-options'] == 'ALLOW-FROM %s' % settings.DOMAIN
    assert 'Last-Modified' in response
    assert response['Last-Modified'] == convert_to_http_date(created)
    assert 'Cache-Control' in response
    assert 'public' in response['Cache-Control']
    assert 'max-age=300' in response['Cache-Control']
    assert 'Vary' not in response


def test_raw_file_if_modified_since(client, settings, file_attachment):
    settings.ATTACHMENT_HOST = 'demos'
    attachment = file_attachment['attachment']
    created = attachment.current_revision.created
    url = attachment.get_file_url()

    response = client.get(
        url,
        HTTP_HOST=settings.ATTACHMENT_HOST,
        HTTP_IF_MODIFIED_SINCE=convert_to_http_date(created)
    )
    assert response.status_code == 304
    assert 'Last-Modified' in response
    assert response['Last-Modified'] == convert_to_http_date(created)
    assert 'Cache-Control' in response
    assert 'public' in response['Cache-Control']
    assert 'max-age=300' in response['Cache-Control']
    assert 'Vary' not in response
