from nose.plugins.attrib import attr
from nose.tools import eq_, ok_
from pyquery import PyQuery as pq

import constance.config
from django.conf import settings

from kuma.users.tests import UserTestCase
from kuma.wiki.tests import revision, WikiTestCase
from kuma.core.urlresolvers import reverse

from ..models import Attachment
from ..utils import make_test_file


class AttachmentTests(UserTestCase, WikiTestCase):

    def setUp(self):
        super(AttachmentTests, self).setUp()
        self.old_allowed_types = constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES
        constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'

    def tearDown(self):
        super(AttachmentTests, self).tearDown()
        constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES = self.old_allowed_types

    @attr('security')
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
        resp = self.client.post(reverse('attachments.new_attachment'),
                                data=post_data)
        eq_(302, resp.status_code)

        # now stick it in/on a document
        attachment = Attachment.objects.get(title=title)
        rev = revision(content='<img src="%s" />' % attachment.get_file_url(),
                       save=True)

        # view it and verify markup is escaped
        response = self.client.get(reverse('wiki.edit_document', args=(rev.slug,),
                                    locale=settings.WIKI_DEFAULT_LANGUAGE))
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('%s xss' % title,
            doc('#page-attachments-table .attachment-name-cell').text())
        ok_('&gt;&lt;img src=x onerror=prompt(navigator.userAgent);&gt;' in
            doc('#page-attachments-table .attachment-name-cell').html())
