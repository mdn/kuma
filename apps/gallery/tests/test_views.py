import json

from django.conf import settings
from django.contrib.auth.models import User

from nose.tools import eq_
from pyquery import PyQuery as pq

from gallery import forms
from gallery.models import Image, Video
from gallery.tests import image, video
from gallery.utils import get_draft_title
from gallery.views import _get_media_info
from sumo.tests import post, LocalizingClient, TestCase
from sumo.urlresolvers import reverse


TEST_IMG = 'apps/upload/tests/media/test.jpg'
TEST_VID = {'webm': 'apps/gallery/tests/media/test.webm',
            'ogv': 'apps/gallery/tests/media/test.ogv',
            'flv': 'apps/gallery/tests/media/test.flv'}
INVALID_VID = 'apps/gallery/tests/media/test.rtf'
VIDEO_PATH = settings.MEDIA_URL + settings.GALLERY_VIDEO_PATH


class DeleteEditImageTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(DeleteEditImageTestCase, self).setUp()
        self.client = LocalizingClient()
        self.client.login(username='jsocol', password='testpass')

    def tearDown(self):
        Image.objects.all().delete()
        super(DeleteEditImageTestCase, self).tearDown()

    def test_delete_image(self):
        """Deleting an uploaded image works."""
        # Upload the image first
        im = image()
        r = post(self.client, 'gallery.delete_media', args=['image', im.id])

        eq_(200, r.status_code)
        eq_(0, Image.objects.count())

    def test_delete_image_without_permissions(self):
        """Can't delete an image I didn't create."""
        self.client.login(username='tagger', password='testpass')
        img = image()
        r = post(self.client, 'gallery.delete_media', args=['image', img.id])

        eq_(403, r.status_code)
        eq_(1, Image.objects.count())

    def test_delete_own_image(self):
        """Can delete an image I created."""
        self.client.login(username='tagger', password='testpass')
        u = User.objects.get(username='tagger')
        img = image(creator=u)
        r = post(self.client, 'gallery.delete_media', args=['image', img.id])

        eq_(200, r.status_code)
        eq_(0, Image.objects.count())

    def test_edit_own_image(self):
        """Can edit an image I created."""
        u = User.objects.get(username='jsocol')
        img = image(creator=u)
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(200, r.status_code)
        eq_('arrr', Image.uncached.get().description)

    def test_edit_image_without_permissions(self):
        """Can't edit an image I didn't create."""
        u = User.objects.get(username='pcraciunoiu')
        img = image(creator=u)
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(403, r.status_code)

    def test_edit_image_with_permissions(self):
        """Editing image sets the updated_by field."""
        self.client.login(username='admin', password='testpass')
        img = image()
        r = post(self.client, 'gallery.edit_media', {'description': 'arrr'},
                 args=['image', img.id])

        eq_(200, r.status_code)
        eq_('admin', Image.objects.get().updated_by.username)


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
        r = post(self.client, 'gallery.upload_async', {'file': ''},
                 args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('You have not selected an image to upload.',
            json_r['errors']['file'][0])

    def test_upload_image(self):
        """Uploading an image works."""
        with open(TEST_IMG) as f:
            r = post(self.client, 'gallery.upload_async', {'file': f},
                     args=['image'])
        img = Image.objects.all()[0]

        eq_(1, Image.objects.count())
        eq_(200, r.status_code)
        json_r = json.loads(r.content)
        eq_('success', json_r['status'])
        file = json_r['file']
        eq_('test.jpg', file['name'])
        eq_(90, file['width'])
        eq_(120, file['height'])
        assert file['url'].endswith(img.get_absolute_url())
        eq_('pcraciunoiu', img.creator.username)
        eq_(150, img.file.width)
        eq_(200, img.file.height)
        eq_(get_draft_title(img.creator), img.title)
        eq_('Autosaved draft.', img.description)
        eq_('en-US', img.locale)

    def test_invalid_image(self):
        """Make sure invalid files are not accepted as images."""
        with open('apps/gallery/__init__.py', 'rb') as f:
            r = post(self.client, 'gallery.upload_async', {'file': f},
                     args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_('Upload a valid image. The file you uploaded was either not an '
            'image or a corrupted image.', json_r['errors']['file'][0])

    def test_upload_image_long_filename(self):
        """Uploading an image with a filename that's too long fails."""
        with open('apps/upload/tests/media/a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_worth_'
                  'more_than_250_characters__a_really_long_filename_yes_.jpg')\
            as f:
            r = post(self.client, 'gallery.upload_async', {'file': f},
                     args=['image'])

        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your image.', json_r['message'])
        eq_(forms.MSG_IMAGE_LONG % {'length': 251,
                                    'max': settings.MAX_FILENAME_LENGTH},
            json_r['errors']['file'][0])

    def test_upload_draft(self):
        """Uploading draft works, sets locale too."""
        u = User.objects.get(username='pcraciunoiu')
        image(creator=u, title=get_draft_title(u))

        r = post(self.client, 'gallery.upload',
                 {'locale': 'de', 'title': 'Hasta la vista',
                  'description': 'Auf wiedersehen!'},
                 args=['image'])

        eq_(200, r.status_code)
        img = Image.objects.all()[0]
        eq_('de', img.locale)
        eq_('Hasta la vista', img.title)
        eq_('Auf wiedersehen!', img.description)


class ViewHelpersTestCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(ViewHelpersTestCase, self).setUp()

    def test_get_media_info_video(self):
        """Gets video and format info."""
        vid = video()
        info_vid, info_format = _get_media_info(vid.pk, 'video')
        eq_(vid.pk, info_vid.pk)
        eq_(None, info_format)

    def test_get_media_info_image(self):
        """Gets image and format info."""
        img = image()
        info_img, info_format = _get_media_info(img.pk, 'image')
        eq_(img.pk, info_img.pk)
        eq_('jpeg', info_format)


class UploadVideoTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(UploadVideoTestCase, self).setUp()
        self.client = LocalizingClient()
        self.client.login(username='pcraciunoiu', password='testpass')

    def tearDown(self):
        Video.objects.all().delete()
        super(UploadVideoTestCase, self).tearDown()

    def _upload_extension(self, ext):
        with open(TEST_VID[ext]) as f:
            r = post(self.client, 'gallery.upload_async', {ext: f},
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
        eq_(32, file['width'])
        eq_(32, file['height'])
        assert file['url'].endswith(vid.get_absolute_url())
        eq_('pcraciunoiu', vid.creator.username)
        eq_(get_draft_title(vid.creator), vid.title)
        eq_('Autosaved draft.', vid.description)
        eq_('en-US', vid.locale)
        with open(TEST_VID['ogv']) as f:
            eq_(f.read(), vid.ogv.read())

    def test_delete_video_ogv(self):
        """Deleting an uploaded video works."""
        # Upload the video first
        self._upload_extension('ogv')
        vid = Video.objects.all()[0]
        r = post(self.client, 'gallery.delete_media',
                 args=['video', vid.id])

        eq_(200, r.status_code)
        eq_(0, Video.objects.count())

    def test_upload_video_ogv_flv(self):
        """Upload the same video, in ogv and flv formats"""
        ogv = open(TEST_VID['ogv'])
        flv = open(TEST_VID['flv'])
        post(self.client, 'gallery.upload_async', {'ogv': ogv, 'flv': flv},
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
        post(self.client, 'gallery.upload_async',
             {'webm': webm, 'ogv': ogv, 'flv': flv}, args=['video'])
        webm.close()
        ogv.close()
        flv.close()
        vid = Video.objects.all()[0]
        eq_(VIDEO_PATH + 'test.webm', vid.webm.url)
        eq_(VIDEO_PATH + 'test.ogv', vid.ogv.url)
        eq_(VIDEO_PATH + 'test.flv', vid.flv.url)

    def test_video_required(self):
        """At least one video format is required to upload."""
        r = post(self.client, 'gallery.upload_async', args=['video'])
        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your video.', json_r['message'])
        eq_('The video has no files associated with it. You must upload one '
            'of the following extensions: webm, ogv, flv.',
            json_r['errors']['__all__'][0])

    def test_upload_video_long_filename(self):
        """Uploading a video with a filename that's too long fails."""
        for k in ('flv', 'ogv', 'webm'):
            with open('apps/upload/tests/media/a_really_long_filename_worth_'
                      'more_than_250_characters__a_really_long_filename_worth_'
                      'more_than_250_characters__a_really_long_filename_worth_'
                      'more_than_250_characters__a_really_long_filename_worth_'
                      'more_than_250_characters__a_really_long_filename_yes_'
                      '.jpg')\
                as f:
                r = post(self.client, 'gallery.upload_async', {k: f},
                         args=['video'])

            eq_(400, r.status_code)
            json_r = json.loads(r.content)
            eq_('error', json_r['status'])
            eq_('Could not upload your video.', json_r['message'])
            message = getattr(forms, 'MSG_' + k.upper() + '_LONG')
            eq_(message % {'length': 251, 'max': settings.MAX_FILENAME_LENGTH},
                json_r['errors'][k][0])

    def test_invalid_video_extension(self):
        """Make sure invalid video extensions are not accepted."""
        with open(INVALID_VID) as f:
            r = post(self.client, 'gallery.upload_async', {'webm': f},
                     args=['video'])
        eq_(400, r.status_code)
        json_r = json.loads(r.content)
        eq_('error', json_r['status'])
        eq_('Could not upload your video.', json_r['message'])
        eq_(forms.MSG_VID_REQUIRED, json_r['errors']['__all__'][0])


class SearchTestCase(TestCase):
    client = LocalizingClient()
    fixtures = ['users.json', 'gallery/media.json']

    def test_search_results(self):
        url = reverse('gallery.search', args=['image'])
        response = self.client.get(url, {'q': 'quicktime'}, follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#media-list li')))

    def test_image_search(self):
        url = reverse('gallery.search', args=['image'])
        response = self.client.get(url, {'q': 'quicktime'}, follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#media-list li')))

    def test_video_search(self):
        url = reverse('gallery.search', args=['video'])
        response = self.client.get(url, {'q': '1802'}, follow=True)
        doc = pq(response.content)
        eq_(1, len(doc('#media-list li')))

    def test_search_description(self):
        url = reverse('gallery.search', args=['image'])
        response = self.client.get(url, {'q': 'migrated'}, follow=True)
        doc = pq(response.content)
        eq_(5, len(doc('#media-list li')))

    def test_search_nonexistent(self):
        url = reverse('gallery.search', args=['foo'])
        response = self.client.get(url, {'q': 'foo'}, follow=True)
        eq_(404, response.status_code)


class GalleryTestCase(TestCase):
    def test_gallery_invalid_type(self):
        url = reverse('gallery.gallery', args=['foo'])
        response = self.client.get(url, follow=True)
        eq_(404, response.status_code)
