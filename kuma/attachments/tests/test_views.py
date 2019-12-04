import datetime
import json
from urllib.parse import urlparse

import pytest
from constance.test import override_config
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from pyquery import PyQuery as pq

from kuma.core.tests import (assert_no_cache_header, assert_redirect_to_wiki,
                             assert_shared_cache_header)
from kuma.core.urlresolvers import reverse
from kuma.core.utils import to_html
from kuma.users.tests import UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import document, revision, WikiTestCase

from . import make_test_file
from ..models import Attachment, AttachmentRevision
from ..utils import convert_to_http_date


@override_config(WIKI_ATTACHMENT_ALLOWED_TYPES='text/plain')
class AttachmentViewTests(UserTestCase, WikiTestCase):

    def setUp(self):
        super(AttachmentViewTests, self).setUp()
        self.client.login(username='admin', password='testpass')
        self.revision = revision(save=True)
        self.document = self.revision.document
        self.files_url = reverse('attachments.edit_attachment',
                                 kwargs={'document_path': self.document.slug})

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
        response = self.client.post(self.files_url, data=post_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        return response

    def test_edit_attachment(self):
        response = self._post_attachment()
        assert_no_cache_header(response)
        assert response.status_code == 302
        assert response['Location'] == self.document.get_edit_url()

        attachment = Attachment.objects.get(title='Test uploaded file')
        rev = attachment.current_revision
        assert rev.creator.username == 'admin'
        assert rev.description == 'A test file uploaded into kuma.'
        assert rev.comment == 'Initial upload'
        assert rev.is_approved

    @override_config(WIKI_ATTACHMENTS_DISABLE_UPLOAD=True)
    def test_disabled_edit_attachment(self):
        response = self._post_attachment()
        assert_no_cache_header(response)
        self.assertEqual(response.status_code, 403)  # HTTP 403 Forbidden
        with self.assertRaises(Attachment.DoesNotExist):
            Attachment.objects.get(title='Test uploaded file')

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
                            ContentFile(b'I am a test file for get_previous'))
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
                            ContentFile(b'I am a test file for get_previous'))
        revision2.save()
        revision2.make_current()

        assert revision1 == revision2.get_previous()

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
        response = self.client.post(self.files_url, data=post_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 200
        assert_no_cache_header(response)
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
                            kwargs={'document_path': doc.slug})
        response = self.client.post(files_url, data=post_data,
                                    HTTP_HOST=settings.WIKI_HOST)
        assert response.status_code == 302
        assert_no_cache_header(response)

        assert doc.files.count() == 1
        intermediates = DocumentAttachment.objects.filter(document__pk=doc.id)
        assert intermediates.count() == 1

        intermediate = intermediates[0]
        assert intermediate.attached_by.username == 'admin'
        assert intermediate.name == file_for_upload.name.split('/')[-1]

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
                           ContentFile(b'I am a test file for get_previous'))
        revision.save()
        revision.make_current()

        feed_url = reverse('attachments.feeds.recent_files',
                           kwargs={'format': 'json'})
        response = self.client.get(feed_url)
        assert_shared_cache_header(response)
        data = json.loads(response.content)
        assert len(data) == 1
        assert data[0]['title'] == revision.title
        assert data[0]['link'] == revision.attachment.get_file_url()
        assert data[0]['author_name'] == test_user.username


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
    assert_shared_cache_header(response)
    assert response['Location'] == file_attachment['attachment'].get_file_url()
    assert not response.has_header('Vary')


def test_edit_attachment_get(admin_client, root_doc):
    url = reverse(
        'attachments.edit_attachment',
        kwargs={'document_path': root_doc.slug})
    response = admin_client.get(url, HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    assert_no_cache_header(response)
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
                  kwargs={'document_path': root_doc.slug})
    response = admin_client.post(url, data=post_data,
                                 HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 200
    doc = pq(response.content)
    assert to_html(doc('ul.errorlist a[href="#id_file"]')) == expected


def test_raw_file_requires_attachment_host(client, settings, file_attachment):
    settings.ATTACHMENT_HOST = 'demos'
    settings.ALLOWED_HOSTS.append('demos')
    attachment = file_attachment['attachment']
    created = attachment.current_revision.created
    url = attachment.get_file_url()

    # Force the HOST header to look like something other than "demos".
    response = client.get(url, HTTP_HOST='testserver')
    assert response.status_code == 301
    assert 'public' in response['Cache-Control']
    assert 'max-age=900' in response['Cache-Control']
    assert response['Location'] == url
    assert 'Vary' not in response

    response = client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
    if settings.ATTACHMENTS_USE_S3:
        # Figure out the external scheme + host for our attachments bucket
        endpoint_url = settings.ATTACHMENTS_AWS_S3_ENDPOINT_URL
        custom_proto = "https" if settings.ATTACHMENTS_AWS_S3_SECURE_URLS else 'http'
        custom_url = f'{custom_proto}://{settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN}'
        bucket_url = custom_url if settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN else endpoint_url

        # Verify we're redirecting to the intended bucket or custom frontend
        assert response.status_code == 302
        assert response['location'].startswith(bucket_url)
    else:
        assert response.status_code == 200
        assert response.streaming

    assert response['x-frame-options'] == f'ALLOW-FROM {settings.DOMAIN}'
    assert response['Last-Modified'] == convert_to_http_date(created)
    assert 'public' in response['Cache-Control']
    assert 'max-age=900' in response['Cache-Control']


def test_raw_file_if_modified_since(client, settings, file_attachment):
    settings.ATTACHMENT_HOST = 'demos'
    settings.ALLOWED_HOSTS.append('demos')
    attachment = file_attachment['attachment']
    created = attachment.current_revision.created
    url = attachment.get_file_url()

    response = client.get(
        url,
        HTTP_HOST=settings.ATTACHMENT_HOST,
        HTTP_IF_MODIFIED_SINCE=convert_to_http_date(created)
    )
    assert response.status_code == 304
    assert response['Last-Modified'] == convert_to_http_date(created)
    assert 'public' in response['Cache-Control']
    assert 'max-age=900' in response['Cache-Control']


def test_edit_attachment_redirect(client, root_doc):
    url = reverse('attachments.edit_attachment',
                  kwargs={'document_path': root_doc.slug})
    response = client.get(url)
    assert_redirect_to_wiki(response, url)
