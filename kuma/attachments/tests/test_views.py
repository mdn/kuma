import datetime

from nose.tools import eq_, ok_

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files import temp as tempfile
from django.utils.http import parse_http_date_safe

from constance import config
from jingo.helpers import urlparams

from kuma.users.tests import UserTestCase
from kuma.wiki.models import Document, DocumentAttachment
from kuma.wiki.tests import document, revision, WikiTestCase
from kuma.core.urlresolvers import reverse

from ..models import Attachment, AttachmentRevision
from ..utils import make_test_file


class AttachmentTests(UserTestCase, WikiTestCase):

    def setUp(self):
        self.old_allowed_types = config.WIKI_ATTACHMENT_ALLOWED_TYPES
        config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'
        super(AttachmentTests, self).setUp()
        self.client.login(username='admin', password='testpass')

    def tearDown(self):
        super(AttachmentTests, self).tearDown()
        config.WIKI_ATTACHMENT_ALLOWED_TYPES = self.old_allowed_types

    def _post_new_attachment(self):
        file_for_upload = make_test_file(
            content='A test file uploaded into kuma.')
        post_data = {
            'title': 'Test uploaded file',
            'description': 'A test file uploaded into kuma.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('attachments.new_attachment'), data=post_data)
        return resp

    def test_legacy_redirect(self):
        test_user = self.user_model.objects.get(username='testuser2')
        test_file_content = 'Meh meh I am a test file.'
        test_files = (
            {'file_id': 97, 'filename': 'Canvas_rect.png',
             'title': 'Canvas rect', 'slug': 'canvas-rect'},
            {'file_id': 107, 'filename': 'Canvas_smiley.png',
             'title': 'Canvas smiley', 'slug': 'canvas-smiley'},
            {'file_id': 86, 'filename': 'Canvas_lineTo.png',
             'title': 'Canvas lineTo', 'slug': 'canvas-lineto'},
            {'file_id': 55, 'filename': 'Canvas_arc.png',
             'title': 'Canvas arc', 'slug': 'canvas-arc'},
        )
        for f in test_files:
            a = Attachment(title=f['title'], slug=f['slug'],
                           mindtouch_attachment_id=f['file_id'])
            a.save()
            now = datetime.datetime.now()
            r = AttachmentRevision(
                attachment=a,
                mime_type='text/plain',
                title=f['title'],
                slug=f['slug'],
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

    def test_new_attachment(self):
        resp = self._post_new_attachment()
        eq_(302, resp.status_code)

        attachment = Attachment.objects.get(title='Test uploaded file')
        eq_(resp['Location'],
            'http://testserver%s' % attachment.get_absolute_url())

        rev = attachment.current_revision
        eq_('admin', rev.creator.username)
        eq_('A test file uploaded into kuma.', rev.description)
        eq_('Initial upload', rev.comment)
        ok_(rev.is_approved)

    def test_edit_attachment(self):
        file_for_upload = make_test_file(
            content='I am a test file for editing.')

        post_data = {
            'title': 'Test editing file',
            'description': 'A test file for editing.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('attachments.new_attachment'), data=post_data)

        tdir = tempfile.gettempdir()
        edited_file_for_upload = tempfile.NamedTemporaryFile(suffix=".txt",
                                                             dir=tdir)
        edited_file_for_upload.write(
            'I am a new version of the test file for editing.')
        edited_file_for_upload.seek(0)

        post_data = {
            'title': 'Test editing file',
            'description': 'A test file for editing.',
            'comment': 'Second revision.',
            'file': edited_file_for_upload,
        }

        attachment = Attachment.objects.get(title='Test editing file')

        resp = self.client.post(reverse('attachments.edit_attachment',
                                        kwargs={
                                            'attachment_id': attachment.id,
                                        }),
                                data=post_data)

        eq_(302, resp.status_code)

        # Re-fetch because it's been updated.
        attachment = Attachment.objects.get(title='Test editing file')
        eq_(resp['Location'],
            'http://testserver%s' % attachment.get_absolute_url())

        eq_(2, attachment.revisions.count())

        rev = attachment.current_revision
        eq_('admin', rev.creator.username)
        eq_('Second revision.', rev.comment)
        ok_(rev.is_approved)

        url = attachment.get_file_url()
        resp = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        eq_('text/plain', rev.mime_type)
        ok_('I am a new version of the test file for editing.' in resp.content)

    def test_attachment_raw_requires_attachment_host(self):
        resp = self._post_new_attachment()
        attachment = Attachment.objects.get(title='Test uploaded file')

        url = attachment.get_file_url()
        resp = self.client.get(url)
        eq_(301, resp.status_code)
        eq_(attachment.get_file_url(), resp['Location'])

        url = attachment.get_file_url()
        resp = self.client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
        eq_('ALLOW-FROM: %s' % settings.DOMAIN, resp['x-frame-options'])
        eq_(200, resp.status_code)
        ok_('Last-Modified' in resp)
        ok_('1970' not in resp['Last-Modified'])
        ok_('GMT' in resp['Last-Modified'])
        ok_(parse_http_date_safe(resp['Last-Modified']) is not None)

    def test_attachment_detail(self):
        file_for_upload = make_test_file(
            content='I am a test file for attachment detail view.')

        post_data = {
            'title': 'Test file for viewing',
            'description': 'A test file for viewing.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('attachments.new_attachment'), data=post_data)

        attachment = Attachment.objects.get(title='Test file for viewing')

        resp = self.client.get(reverse('attachments.attachment_detail',
                                       kwargs={
                                           'attachment_id': attachment.id,
                                       }))
        eq_(200, resp.status_code)

    def test_get_previous(self):
        """
        AttachmentRevision.get_previous() should return this revisions's
        files's most recent approved revision."""
        test_user = self.user_model.objects.get(username='testuser2')
        a = Attachment(title='Test attachment for get_previous',
                       slug='test-attachment-for-get-previous')
        a.save()
        r = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            slug=a.slug,
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
            slug=a.slug,
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

    def test_mime_type_filtering(self):
        """Don't allow uploads outside of the explicitly-permitted
        mime-types."""
        # SLIGHT HACK: this requires the default set of allowed
        # mime-types specified in settings.py. Specifically, adding
        # 'text/html' to that set will make this test fail.
        test_user = self.user_model.objects.get(username='testuser2')
        a = Attachment(title='Test attachment for file type filter',
                       slug='test-attachment-for-file-type-filter')
        a.save()
        r = AttachmentRevision(
            attachment=a,
            mime_type='text/plain',
            title=a.title,
            slug=a.slug,
            description='',
            comment='Initial revision.',
            created=datetime.datetime.now() - datetime.timedelta(seconds=30),
            creator=test_user,
            is_approved=True)
        r.file.save('mime_type_filter_test_file.txt',
                    ContentFile('I am a test file for mime-type filtering'))

        # Shamelessly stolen from Django's own file-upload tests.
        tdir = tempfile.gettempdir()
        file_for_upload = tempfile.NamedTemporaryFile(suffix=".html",
                                                      dir=tdir)
        file_for_upload.write('<html>I am a file that tests'
                              'mime-type filtering.</html>.')
        file_for_upload.seek(0)

        post_data = {
            'title': 'Test disallowed file type',
            'description': 'A file kuma should disallow on type.',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        resp = self.client.post(reverse('attachments.edit_attachment',
                                        kwargs={'attachment_id': a.id}),
                                data=post_data)
        eq_(200, resp.status_code)
        ok_('Files of this type are not permitted.' in resp.content)

    def test_intermediate(self):
        """
        Test that the intermediate DocumentAttachment gets created
        correctly when adding an Attachment with a document_id.

        """
        doc = document(locale='en', slug='attachment-test-intermediate')
        doc.save()
        rev = revision(document=doc, is_approved=True)
        rev.save()

        file_for_upload = make_test_file(
            content='A file for testing intermediate attachment model.')

        post_data = {
            'title': 'Intermediate test file',
            'description': 'Intermediate test file',
            'comment': 'Initial upload',
            'file': file_for_upload,
        }

        add_url = urlparams(reverse('attachments.new_attachment'),
                            document_id=doc.id)
        resp = self.client.post(add_url, data=post_data)
        eq_(302, resp.status_code)

        eq_(1, doc.files.count())

        intermediates = DocumentAttachment.objects.filter(document__pk=doc.id)
        eq_(1, intermediates.count())

        intermediate = intermediates[0]
        eq_('admin', intermediate.attached_by.username)
        eq_(file_for_upload.name.split('/')[-1], intermediate.name)

    def test_files_dict(self):
        doc = document(locale='en', slug='attachment-test-files-dict')
        doc.save()
        rev = revision(document=doc, is_approved=True)
        rev.save()

        test_file_1 = make_test_file(
            content='A file for testing the files dict')

        post_data = {
            'title': 'Files dict test file',
            'description': 'Files dict test file',
            'comment': 'Initial upload',
            'file': test_file_1,
        }

        add_url = urlparams(reverse('attachments.new_attachment'),
                            document_id=doc.id)
        self.client.post(add_url, data=post_data)

        test_file_2 = make_test_file(
            content='Another file for testing the files dict')

        post_data = {
            'title': 'Files dict test file 2',
            'description': 'Files dict test file 2',
            'comment': 'Initial upload',
            'file': test_file_2,
        }

        self.client.post(add_url, data=post_data)

        doc = Document.objects.get(pk=doc.id)

        files_dict = doc.files_dict()

        file1 = files_dict[test_file_1.name.split('/')[-1]]
        eq_('admin', file1['attached_by'])
        eq_('Files dict test file', file1['description'])
        eq_('text/plain', file1['mime_type'])
        ok_(test_file_1.name.split('/')[-1] in file1['url'])

        file2 = files_dict[test_file_2.name.split('/')[-1]]
        eq_('admin', file2['attached_by'])
        eq_('Files dict test file 2', file2['description'])
        eq_('text/plain', file2['mime_type'])
        ok_(test_file_2.name.split('/')[-1] in file2['url'])

    def test_list_files(self):
        list_files_url = reverse('attachments.list_files',
                                 locale=settings.WIKI_DEFAULT_LANGUAGE)
        resp = self.client.get(list_files_url)
        eq_(200, resp.status_code)
        ok_('All Files' in resp.content)
