import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.test import client, TestCase

from nose.tools import eq_

from questions.models import Question
from sumo.urlresolvers import reverse
from upload.models import ImageAttachment
from upload.utils import (scale_dimensions, create_thumbnail,
                          create_image_attachment)


post = lambda c, v, data={}, **kw: c.post(reverse(v, **kw), data, follow=True)


class ScaleDimensionsTestCase(TestCase):

    def test_basic(self):
        """A square image of exact size is not scaled."""
        ts = settings.THUMBNAIL_SIZE
        (width, height) = scale_dimensions(ts, ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_small(self):
        """A small image is not scaled."""
        ts = settings.THUMBNAIL_SIZE / 2
        (width, height) = scale_dimensions(ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_width_large(self):
        """An image with large width is scaled to width=MAX."""
        ts = 120
        (width, height) = scale_dimensions(ts * 3 + 10, ts - 1, ts)
        eq_(ts, width)
        eq_(38, height)

    def test_large_height(self):
        """An image with large height is scaled to height=MAX."""
        ts = 150
        (width, height) = scale_dimensions(ts - 2, ts * 2 + 9, ts)
        eq_(71, width)
        eq_(ts, height)

    def test_large_both_height(self):
        """An image with both large is scaled to the largest - height."""
        ts = 150
        (width, height) = scale_dimensions(ts * 2 + 13, ts * 5 + 30, ts)
        eq_(60, width)
        eq_(ts, height)

    def test_large_both_width(self):
        """An image with both large is scaled to the largest - width."""
        ts = 150
        (width, height) = scale_dimensions(ts * 20 + 8, ts * 4 + 36, ts)
        eq_(ts, width)
        eq_(31, height)


class CreateThumbnailTestCase(TestCase):

    def test_basic(self):
        """A thumbnail is created from an image file."""
        thumb_content = create_thumbnail('apps/upload/tests/media/test.jpg')
        f = open('apps/upload/tests/media/test_thumb.jpg')
        eq_(thumb_content.read(), f.read())
        f.close()


class CreateImageAttachmentTestCase(TestCase):
    fixtures = ['users.json', 'questions.json', 'content_types.json']

    def setUp(self):
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]

    def tearDown(self):
        ImageAttachment.objects.all().delete()

    def test_basic(self):
        """
        An image attachment is created from an uploaded file.

        Verifies all appropriate fields are correctly set.
        """
        f = open('apps/upload/tests/media/test.jpg')
        up_file = File(f)
        image = create_image_attachment(up_file, self.obj, self.user)
        f.close()

        eq_(settings.IMAGE_UPLOAD_PATH + 'test.jpg', image.file.name)
        eq_(150, image.file.width)
        eq_(200, image.file.height)
        eq_(self.obj.id, image.object_id)
        eq_(22, image.content_type.id)  # Question content type
        eq_(self.user, image.creator)
        eq_(90, image.thumbnail.width)
        eq_(120, image.thumbnail.height)


class UploadImageTestCase(TestCase):
    fixtures = ['users.json', 'questions.json', 'content_types.json']

    def setUp(self):
        self.client = client.Client()
        self.client.get('/')
        self.client.login(username='pcraciunoiu', password='testpass')

    def tearDown(self):
        ImageAttachment.objects.all().delete()

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
        f = open('apps/upload/tests/media/test.jpg')
        r = post(self.client, 'upload.up_image_async', {'image': f},
                 args=['questions.Question', 1])
        f.close()

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
        eq_(90, image.thumbnail.width)
        eq_(120, image.thumbnail.height)
        eq_('question', image.content_type.model)
        eq_(1, image.object_id)

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
