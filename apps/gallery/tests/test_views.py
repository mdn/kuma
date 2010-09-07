import json

from django.conf import settings

from nose.tools import eq_
from nose import SkipTest

from sumo.tests import post, LocalizingClient, TestCase
from gallery.models import Image, Video


TEST_IMG = 'apps/upload/tests/media/test.jpg'
TEST_VID = {'webm': 'apps/gallery/tests/media/test.webm',
            'ogv': 'apps/gallery/tests/media/test.ogv',
            'flv': 'apps/gallery/tests/media/test.flv'}
VIDEO_PATH = settings.MEDIA_URL + settings.GALLERY_VIDEO_PATH


class UploadImageTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(UploadImageTestCase, self).setUp()
        self.client = LocalizingClient()
        self.client.login(username='pcraciunoiu', password='testpass')

    def tearDown(self):
        Image.objects.all().delete()
        super(UploadImageTestCase, self).tearDown()

    def test_empty_image(self):
        """Specifying an invalid model returns 400."""
        r = post(self.client, 'gallery.up_media_async', {'file': ''},
                 args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('You have not selected an image to upload.',
            json_r['errors']['file'][0])

    def test_empty_title(self):
        """Title is required when uploading."""
        with open(TEST_IMG) as f:
            r = post(self.client, 'gallery.up_media_async', {'file': f},
                     args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('Please provide a title.', json_r['errors']['title'][0])

    def test_empty_description(self):
        """Description is required when uploading."""
        with open(TEST_IMG) as f:
            r = post(self.client, 'gallery.up_media_async',
                     {'file': f, 'title': 'Title'}, args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('Please provide a description.',
            json_r['errors']['description'][0])

    def test_upload_image(self):
        """Uploading an image works."""
        with open(TEST_IMG) as f:
            r = post(self.client, 'gallery.up_media_async',
                     {'file': f, 'title': 'Title', 'description': 'Test'},
                     args=['image'])
        image = Image.objects.all()[0]

        eq_(1, Image.objects.count())
        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['file']
        eq_('test.jpg', file['name'])
        eq_(90, file['width'])
        eq_(120, file['height'])
        assert file['url'].endswith(image.get_absolute_url())
        eq_('pcraciunoiu', image.creator.username)
        eq_(150, image.file.width)
        eq_(200, image.file.height)
        eq_('Title', image.title)
        eq_('Test', image.description)
        eq_('en-US', image.locale)

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        # Upload the image first
        self.test_upload_image()
        im = Image.objects.all()[0]
        r = post(self.client, 'gallery.del_media_async', args=['image', im.id])

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        eq_(0, Image.objects.count())

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open('apps/gallery/__init__.py', 'rb') as f:
            r = post(self.client, 'gallery.up_media_async', {'file': f},
                     args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('Upload a valid image. The file you uploaded was either not an '
            'image or a corrupted image.', json_r['errors']['file'][0])


class UploadVideoTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(UploadVideoTestCase, self).setUp()
        self.client = LocalizingClient()
        self.client.login(username='pcraciunoiu', password='testpass')

    def tearDown(self):
        Video.objects.all().delete()
        super(UploadVideoTestCase, self).tearDown()

    def test_empty_title(self):
        """Title is required when uploading."""
        with open(TEST_VID['ogv']) as f:
            r = post(self.client, 'gallery.up_media_async', {'ogv': f},
                     args=['video'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your video.', json_r['message'])
        eq_('Please provide a title.', json_r['errors']['title'][0])

    def test_empty_description(self):
        """Description is required when uploading."""
        with open(TEST_VID['flv']) as f:
            r = post(self.client, 'gallery.up_media_async',
                     {'flv': f, 'title': 'Title'}, args=['video'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your video.', json_r['message'])
        eq_('Please provide a description.',
            json_r['errors']['description'][0])

    def _upload_extension(self, ext):
        with open(TEST_VID[ext]) as f:
            r = post(self.client, 'gallery.up_media_async',
                     {ext: f, 'title': 'Title', 'description': 'Test'},
                     args=['video'])
        return r

    def test_upload_video(self):
        """Uploading a video works."""
        r = self._upload_extension('ogv')
        vid = Video.objects.all()[0]

        eq_(1, Video.objects.count())
        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['file']
        eq_('test.ogv', file['name'])
        eq_(120, file['width'])
        eq_(120, file['height'])
        assert file['url'].endswith(vid.get_absolute_url())
        eq_('pcraciunoiu', vid.creator.username)
        eq_('Title', vid.title)
        eq_('Test', vid.description)
        eq_('en-US', vid.locale)
        with open(TEST_VID['ogv']) as f:
            eq_(f.read(), vid.ogv.read())

    def test_delete_video_ogv(self):
        """Deleting an uploaded video works."""
        # Upload the video first
        self._upload_extension('ogv')
        vid = Video.objects.all()[0]
        r = post(self.client, 'gallery.del_media_async',
                 args=['video', vid.id])

        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        eq_(0, Video.objects.count())

    def test_upload_video_ogv_flv(self):
        """Upload the same video, in ogv and flv formats"""
        ogv = open(TEST_VID['ogv'])
        flv = open(TEST_VID['flv'])
        post(self.client, 'gallery.up_media_async',
             {'ogv': ogv, 'flv': flv, 'title': 'Title', 'description': 'Test'},
             args=['video'])
        ogv.close()
        flv.close()
        vid = Video.objects.all()[0]
        eq_(VIDEO_PATH + 'test.ogv', vid.ogv.url)
        eq_(VIDEO_PATH + 'test.flv', vid.flv.url)

    def test_upload_video_all(self):
        """Upload the same video, in all formats"""
        webm = open(TEST_VID['webm'])
        ogv = open(TEST_VID['ogv'])
        flv = open(TEST_VID['flv'])
        post(self.client, 'gallery.up_media_async',
             {'webm': webm, 'ogv': ogv, 'flv': flv,
              'title': 'Title', 'description': 'Test'}, args=['video'])
        webm.close()
        ogv.close()
        flv.close()
        vid = Video.objects.all()[0]
        eq_(VIDEO_PATH + 'test.webm', vid.webm.url)
        eq_(VIDEO_PATH + 'test.ogv', vid.ogv.url)
        eq_(VIDEO_PATH + 'test.flv', vid.flv.url)

    def test_video_required(self):
        """At least one video format is required to upload."""
        r = post(self.client, 'gallery.up_media_async',
                 {'title': 'Title', 'description': 'Test'}, args=['video'])
        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your video.', json_r['message'])
        eq_('The video has no files associated with it. You must upload one '
            'of the following extensions: webm, ogv, flv.',
            json_r['errors']['__all__'][0])

    def test_invalid_video_webm(self):
        """Make sure invalid webm videos are not accepted."""
        raise SkipTest

    def test_invalid_video_ogv(self):
        """Make sure invalid ogv videos are not accepted."""
        raise SkipTest

    def test_invalid_video_flv(self):
        """Make sure invalid flv videos are not accepted."""
        raise SkipTest
