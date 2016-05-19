import pytest
from constance import config
from pyquery import PyQuery as pq

from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase
from kuma.wiki.tests import document, revision, WikiTestCase

from ..models import Attachment
from . import make_test_file


class AttachmentTemplatesTests(UserTestCase, WikiTestCase):

    def setUp(self):
        super(AttachmentTemplatesTests, self).setUp()
        self.old_allowed_types = config.WIKI_ATTACHMENT_ALLOWED_TYPES
        config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'
        self.client.login(username='admin', password='testpass')
        self.document = document(save=True)
        self.files_url = reverse('attachments.edit_attachment',
                                 kwargs={'document_path': self.document.slug},
                                 locale='en-US')

    def tearDown(self):
        super(AttachmentTemplatesTests, self).tearDown()
        config.WIKI_ATTACHMENT_ALLOWED_TYPES = self.old_allowed_types

    @pytest.mark.security
    def test_xss_file_attachment_title(self):
        title = '"><img src=x onerror=prompt(navigator.userAgent);>'
        # use view to create new attachment
        file_for_upload = make_test_file()
        post_data = {
            'title': title,
            'description': 'xss',
            'comment': 'xss',
            'file': file_for_upload,
        }
        self.client.login(username='admin', password='testpass')
        response = self.client.post(self.files_url, data=post_data)
        self.assertEqual(response.status_code, 302)

        # now stick it in/on a document
        attachment = Attachment.objects.get(title=title)
        rev = revision(content='<img src="%s" />' % attachment.get_file_url(),
                       document=self.document,
                       save=True)

        # view it and verify markup is escaped
        response = self.client.get(rev.document.get_edit_url())
        self.assertEqual(response.status_code, 200)
        doc = pq(response.content)
        self.assertEqual(
            '%s xss' % title,
            doc('.page-attachments-table .attachment-name-cell').text()
        )
        self.assertIn(
            '&gt;&lt;img src=x onerror=prompt(navigator.userAgent);&gt;',
            doc('.page-attachments-table .attachment-name-cell').html()
        )
        # security bug 1272791
        for script in doc('script'):
            self.assertNotIn(title, script.text_content())
