import json

from django.conf import settings

from nose.tools import eq_

from sumo.tests import post, LocalizingClient, TestCase
from upload.forms import MSG_IMAGE_LONG
from upload.models import ImageAttachment


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

    def test_invalid_image_extensions(self):
        """Make sure invalid extensions are not accepted as images."""
        with open('apps/upload/tests/media/test_invalid.ext', 'rb') as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_('Please upload an image with one of the following extensions: '
            'jpg, jpeg, png, gif.', json_r['errors']['__all__'][0])

    def test_upload_long_filename(self):
        """Uploading an image with a filename that's too long fails."""
        with open('apps/upload/tests/media/a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_yes_.jpg')\
            as f:
            r = post(self.client, 'upload.up_image_async', {'image': f},
                     args=['questions.Question', 1])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Invalid or no image received.', json_r['message'])
        eq_(MSG_IMAGE_LONG % {'length': 251,
                              'max': settings.MAX_FILENAME_LENGTH},
            json_r['errors']['image'][0])
