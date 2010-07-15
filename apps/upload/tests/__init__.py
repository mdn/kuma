import json

from django.test import client, TestCase

from nose.tools import eq_

from sumo.urlresolvers import reverse


post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class UploadImageTestCase(TestCase):

    def setUp(self):
        """Setup"""

        self.client = client.Client()
        self.client.get('/')

    def test_empty_html(self):
        """Upload nothing returns 500 error and html content."""
        r = post(self.client, 'upload.up_image', {'image': ''})

        eq_(500, r.status_code)
        eq_('Invalid or no image received.', r.content)

    def test_basic_html(self):
        f = open('apps/upload/tests/media/test.jpg')
        r = post(self.client, 'upload.up_image', {'image': f})
        f.close()

        eq_(200, r.status_code)
        assert r.content.startswith('<!DOCTYPE'), ('Unexpected content, "%s"' %
                                                   r.content)

    def test_empty_json(self):
        """Upload nothing returns 500 error and json content."""
        t_url = "%s?X-Requested-With=iframe" % reverse('upload.up_image')
        r = self.client.post(t_url, {'image': ''})

        eq_(500, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])

    def test_basic_json(self):
        t_url = "%s?X-Requested-With=iframe" % reverse('upload.up_image')
        f = open('apps/upload/tests/media/test.jpg')
        r = self.client.post(t_url, {'image': f})
        f.close()

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        assert json_r['filename'].endswith('test.jpg'), (
            'Unexpected content, "%s"' % r.content)

    def test_blank_html(self):
        """Just access the URL."""
        r = self.client.get(reverse('upload.up_image'))

        eq_(500, r.status_code)
        eq_('Invalid or no image received.', r.content)

    def test_blank_json(self):
        """Just access the URL."""
        t_url = "%s?X-Requested-With=iframe" % reverse('upload.up_image')
        r = self.client.get(t_url)

        eq_(500, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
