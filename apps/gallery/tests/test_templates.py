from django.contrib.auth.models import User

from nose import SkipTest
from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.helpers import urlparams
from sumo.tests import TestCase, get, LocalizingClient, post
from sumo.urlresolvers import reverse
from gallery.models import Image, Video
from gallery.tests import image, video
from gallery.utils import get_draft_title


class GalleryPageCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Image.objects.all().delete()
        super(GalleryPageCase, self).tearDown()

    def test_gallery_images(self):
        """Test that all images show up on images gallery page.

        Also, Make sure they don't show up on videos page.

        """
        img = image()
        response = get(self.client, 'gallery.gallery', args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))
        eq_(img.thumbnail_url_if_set(), imgs[0].attrib['src'])

    def test_gallery_locale(self):
        """Test that images only show for their set locale."""
        image(locale='es')
        url = reverse('gallery.gallery', args=['image'])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(0, len(imgs))

        locale_url = reverse('gallery.gallery', locale='es',
                             args=['image'])
        response = self.client.get(locale_url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))

    def test_gallery_upload_modal(self):
        # TODO(paul) this will probably be broken up into separate tests:
        # * Upload modal has the URL's locale selected
        # * POSTing invalid data shows error messages and pre-fills that data
        raise SkipTest


class GalleryAsyncCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Image.objects.all().delete()
        super(GalleryAsyncCase, self).tearDown()

    def test_gallery_image_list(self):
        """Test for ajax endpoint without search parameter."""
        img = image()
        url = urlparams(reverse('gallery.async'), type='image')
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))
        eq_(img.thumbnail_url_if_set(), imgs[0].attrib['src'])

    def test_gallery_image_search(self):
        """Test for ajax endpoint with search parameter."""
        img = image()
        url = urlparams(reverse('gallery.async'), type='image', q='foobar')
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(0, len(imgs))

        url = urlparams(reverse('gallery.async'), type='image', q=img.title)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))
        eq_(img.thumbnail_url_if_set(), imgs[0].attrib['src'])


class GalleryUploadTestCase(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        super(GalleryUploadTestCase, self).setUp()
        self.client = LocalizingClient()
        self.client.login(username='pcraciunoiu', password='testpass')
        self.u = User.objects.get(username='pcraciunoiu')

    def tearDown(self):
        Image.objects.all().delete()
        Video.objects.all().delete()
        super(GalleryUploadTestCase, self).tearDown()

    def test_image_draft_shows(self):
        """The image draft is loaded for this user."""
        image(title=get_draft_title(self.u), creator=self.u)
        response = get(self.client, 'gallery.gallery', args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert 'images/test' in doc('.image-preview img').attr('src')
        eq_(1, doc('.image-preview img').length)

    def test_video_draft_shows(self):
        """The video draft is loaded for this user."""
        video(title=get_draft_title(self.u), creator=self.u)
        response = get(self.client, 'gallery.gallery', args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        # Preview for all 3 video formats: flv, ogv, webm
        eq_(3, doc('ul li.video-preview').length)

    def test_image_draft_post(self):
        """Posting to the page saves the field values for the image draft."""
        image(title=get_draft_title(self.u), creator=self.u)
        response = post(self.client, 'gallery.gallery',
                        {'description': '??', 'title': 'test'}, args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        # Preview for all 3 video formats: flv, ogv, webm
        eq_('??', doc('#gallery-upload-modal textarea').html())
        eq_('test', doc('#gallery-upload-modal input[name="title"]').val())

    def test_video_draft_post(self):
        """Posting to the page saves the field values for the video draft."""
        video(title=get_draft_title(self.u), creator=self.u)
        response = post(self.client, 'gallery.gallery',
                        {'title': 'zTestz'}, args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        # Preview for all 3 video formats: flv, ogv, webm
        eq_('zTestz', doc('#gallery-upload-modal input[name="title"]').val())


class MediaPageCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Image.objects.all().delete()
        super(MediaPageCase, self).tearDown()

    def test_image_media_page(self):
        """Test the media page."""
        img = image()
        response = self.client.get(img.get_absolute_url(), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(img.title, doc('#media-object h1').text())
        eq_(img.description, doc('#media-object div.description').text())
        eq_(img.file.url, doc('#media-view img')[0].attrib['src'])
