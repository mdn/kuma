import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.test import TestCase

from nose.tools import eq_

from questions.models import Question
from sumo.tests import post, LocalizingClient, TestCase
from upload.models import ImageAttachment
from upload.utils import create_image_attachment


class CreateImageAttachmentTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(CreateImageAttachmentTestCase, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]
        self.ct = ContentType.objects.get_for_model(self.obj)

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(CreateImageAttachmentTestCase, self).tearDown()

    def test_basic(self):
        """
        An image attachment is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            image = create_image_attachment(up_file, self.obj, self.user)

        message = 'File name "%s" does not contain "test"' % image.file.name
        assert 'test' in image.file.name, message
        eq_(150, image.file.width)
        eq_(200, image.file.height)
        eq_(self.obj.id, image.object_id)
        eq_(self.ct.id, image.content_type.id)
        eq_(self.user, image.creator)


class UploadImageTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(UploadImageTestCase, self).setUp()
        self.client = LocalizingClient()
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
        with open('apps/upload/tests/media/test.jpg') as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['files'][0]
        eq_('test.jpg', file['name'])
        eq_(90, file['width'])
        eq_(120, file['height'])
        message = 'Url "%s" does not contain "test"' % file['url']
        assert ('test' in file['url']), message

        eq_(1, ImageAttachment.objects.count())
        image = ImageAttachment.objects.all()[0]
        eq_('pcraciunoiu', image.creator.username)
        eq_(150, image.file.width)
        eq_(200, image.file.height)
        eq_('question', image.content_type.model)
        eq_(1, image.object_id)

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open('apps/upload/__init__.py', 'rb') as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
