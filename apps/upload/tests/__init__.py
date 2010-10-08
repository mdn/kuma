import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File

from nose.tools import eq_

from questions.models import Question
from sumo.tests import post, LocalizingClient, TestCase
from upload.models import ImageAttachment
from upload.utils import (create_imageattachment, check_file_size,
                          FileTooLargeError)


def check_file_info(file_info, name, width, height, delete_url, url,
                    thumbnail_url):
    eq_(name, file_info['name'])
    eq_(width, file_info['width'])
    eq_(height, file_info['height'])
    eq_(delete_url, file_info['delete_url'])
    eq_(url, file_info['url'])
    eq_(thumbnail_url, file_info['thumbnail_url'])


class CheckFileSizeTestCase(TestCase):
    """Tests for check_file_size"""
    def test_check_file_size_under(self):
        """No exception should be raised"""
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    def test_check_file_size_over(self):
        """FileTooLargeError should be raised"""
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            fn = lambda: check_file_size(up_file, 0)
            self.assertRaises(FileTooLargeError, fn)


class CreateImageAttachmentTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(CreateImageAttachmentTestCase, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(CreateImageAttachmentTestCase, self).tearDown()

    def test_create_imageattachment(self):
        """
        An image attachment is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            file_info = create_imageattachment(
                {'image': up_file}, self.user, self.obj)

        image = ImageAttachment.objects.all()[0]
        check_file_info(
            file_info, name='apps/upload/tests/media/test.jpg',
            width=90, height=120, delete_url=image.get_delete_url(),
            url=image.get_absolute_url(), thumbnail_url=image.thumbnail.url)


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
        eq_('You have not selected an image to upload.',
            json_r['errors']['image'][0])

    def test_upload_image(self):
        """Uploading an image works."""
        with open('apps/upload/tests/media/test.jpg') as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['file']
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

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        # Upload the image first
        self.test_upload_image()
        im = ImageAttachment.objects.all()[0]
        r = post(self.client, 'upload.del_image_async', args=[im.id])

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        eq_(0, ImageAttachment.objects.count())

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open('apps/upload/__init__.py', 'rb') as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_('The submitted file is empty.', json_r['errors']['image'][0])
