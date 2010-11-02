from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import TestCase, get
from sumo.urlresolvers import reverse
from gallery.models import Image
from gallery.tests import image


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
        response = get(self.client, 'gallery.gallery_media',
                       args=['image'])
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))
        eq_(img.thumbnail_url_if_set(), imgs[0].attrib['src'])

    def test_gallery_locale(self):
        """Test that images only show for their set locale."""
        image(locale='es')
        url = reverse('gallery.gallery_media', args=['image'])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(0, len(imgs))

        locale_url = reverse('gallery.gallery_media', locale='es',
                             args=['image'])
        response = self.client.get(locale_url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('#media-list li img')
        eq_(1, len(imgs))


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
