import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.test import client, TestCase

from nose.tools import eq_
from nose.plugins.skip import SkipTest

from questions.models import Question
from sumo.urlresolvers import reverse
from upload.models import ImageAttachment
from upload.utils import create_image_attachment


post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class CreateImageAttachmentTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(CreateImageAttachmentTestCase, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(CreateImageAttachmentTestCase, self).tearDown()

    def test_basic(self):
        """
        An image attachment is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        # TODO: upload.utils.create_image_attachment creates an ImageAttachment
        raise SkipTest


class UploadImageTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(UploadImageTestCase, self).setUp()
        self.client = client.Client()
        self.client.get('/')
        self.client.login(username='pcraciunoiu', password='testpass')

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(UploadImageTestCase, self).tearDown()

    def test_model_invalid(self):
        """Specifying an invalid model returns 400."""
        r = post(self.client, 'upload.up_image_async', {'image': ''},
                 args=['invalid.model', 123])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Model does not exist.', json_r['message'])

    def test_object_notexist(self):
        """Upload nothing returns 404 error and html content."""
        r = post(self.client, 'upload.up_image_async', {'image': ''},
                 args=['questions.Question', 123])

        eq_(404, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Object does not exist.', json_r['message'])

    def test_empty_image(self):
        """Upload nothing returns 400 error and json content."""
        r = post(self.client, 'upload.up_image_async', {'image': ''},
                 args=['questions.Question', 1])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])

    def test_basic(self):
        """Uploading an image works."""
        # TODO: posting a valid image through the test client uploads it
        raise SkipTest

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        f = open('apps/upload/__init__.py', 'rb')
        r = post(self.client, 'upload.up_image_async', {'image': f},
                 args=['questions.Question', 1])
        f.close()

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
