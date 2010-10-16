from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File

from nose.tools import eq_

from questions.models import Question
from sumo.tests import TestCase
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
