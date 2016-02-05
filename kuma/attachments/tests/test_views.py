import datetime

from constance.test import override_config
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.http import parse_http_date_safe

from kuma.core.urlresolvers import reverse
from kuma.core.tests import eq_, ok_
from kuma.users.tests import UserTestCase
from kuma.wiki.models import DocumentAttachment
from kuma.wiki.tests import WikiTestCase, document, revision

from ..models import Attachment, AttachmentRevision
from . import make_test_file


@override_config(WIKI_ATTACHMENT_ALLOWED_TYPES='text/plain')
class AttachmentTests(UserTestCase, WikiTestCase):

    def setUp(self):
        super(AttachmentTests, self).setUp()
        self.client.login(username='admin', password='testpass')
        self.document = document(save=True)
        self.files_url = reverse('attachments.edit_attachment',
                                 kwargs={'document_path': self.document.slug},
                                 locale='en-US')

    def _post_attachment(self):
        file_for_upload = make_test_file(
            content='A test file uploaded into kuma.')
        post_data = {
            'title': 'Test uploaded file',
            'description': 'A test file uploaded into kuma.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }
        resp = self.client.post(self.files_url, data=post_data)
        return resp

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
        for f in test_files:
            a = Attachment(title=f['title'],
                           mindtouch_attachment_id=f['file_id'])
            a.save()
            now = datetime.datetime.now()
            r = AttachmentRevision(
                attachment=a,
                mime_type='text/plain',
                title=f['title'],
                description='',
                created=now,
                is_approved=True)
            r.creator = test_user
            r.file.save(f['filename'], ContentFile(test_file_content))
            r.make_current()
            mindtouch_url = reverse('attachments.mindtouch_file_redirect',
                                    args=(),
                                    kwargs={'file_id': f['file_id'],
                                            'filename': f['filename']})
            resp = self.client.get(mindtouch_url)
            eq_(301, resp.status_code)
            ok_(a.get_file_url() in resp['Location'])

    def test_edit_attachment(self):
        resp = self._post_attachment()
        eq_(302, resp.status_code)

        attachment = Attachment.objects.get(title='Test uploaded file')
        eq_(resp['Location'],
            'http://testserver%s' % self.document.get_edit_url())

        rev = attachment.current_revision
        eq_('admin', rev.creator.username)
        eq_('A test file uploaded into kuma.', rev.description)
        eq_('Initial upload', rev.comment)
        ok_(rev.is_approved)

    def test_attachment_raw_requires_attachment_host(self):
        resp = self._post_attachment()
        attachment = Attachment.objects.get(title='Test uploaded file')

        url = attachment.get_file_url()
        resp = self.client.get(url)
        eq_(301, resp.status_code)
        eq_(attachment.get_file_url(), resp['Location'])

        url = attachment.get_file_url()
        resp = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        ok_(resp.streaming)
        eq_('ALLOW-FROM: %s' % settings.DOMAIN, resp['x-frame-options'])
        eq_(200, resp.status_code)
        ok_('Last-Modified' in resp)
        ok_('1970' not in resp['Last-Modified'])
        ok_('GMT' in resp['Last-Modified'])
        ok_(parse_http_date_safe(resp['Last-Modified']) is not None)

    def test_get_previous(self):
        """
        AttachmentRevision.get_previous() should return this revisions's
        files's most recent approved revision."""
        test_user = self.user_model.objects.get(username='testuser2')
        a = Attachment(title='Test attachment for get_previous')
        a.save()
        r = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        r.file.save('get_previous_test_file.txt',
                    ContentFile('I am a test file for get_previous'))
        r.save()
        r.make_current()

        r2 = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            description='',
            comment='First edit..',
            created=datetime.datetime.now(),
            creator=test_user,
            is_approved=True)
        r2.file.save('get_previous_test_file.txt',
                     ContentFile('I am a test file for get_previous'))
        r2.save()
        r2.make_current()

        eq_(r, r2.get_previous())

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
        resp = self.client.post(self.files_url, data=post_data)
        eq_(200, resp.status_code)
        ok_('Files of this type are not permitted.' in resp.content)
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
        resp = self.client.post(files_url, data=post_data)
        eq_(302, resp.status_code)

        eq_(1, doc.files.count())
        intermediates = DocumentAttachment.objects.filter(document__pk=doc.id)
        eq_(1, intermediates.count())

        intermediate = intermediates[0]
        eq_('admin', intermediate.attached_by.username)
        eq_(file_for_upload.name.split('/')[-1], intermediate.name)
