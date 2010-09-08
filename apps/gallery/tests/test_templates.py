from nose.tools import eq_
from pyquery import PyQuery as pq

from sumo.tests import TestCase
from sumo.tests import get
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from gallery.tests import image


class GalleryPageCase(TestCase):

    def test_gallery_images(self):
        """Test that all images show up on images gallery page.

        Also, Make sure they don't show up on videos page.

        """
        img = image()
        response = get(self.client, 'gallery.gallery_images')
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('section.gallery li img')
        eq_(1, len(imgs))
        eq_(img.thumbnail_or_file().url, imgs[0].attrib['src'])

    def test_gallery_locale(self):
        """Test that images only show for their set locale."""
        image(locale='es')
        url = reverse('gallery.gallery_images')
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('section.gallery li img')
        eq_(0, len(imgs))

        locale_url = urlparams(url, locale='es')
        response = self.client.get(locale_url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        imgs = doc('section.gallery li img')
        eq_(1, len(imgs))


class MediaPageCase(TestCase):

    def test_image_media_page(self):
        """Test the media page."""
        img = image()
        response = self.client.get(img.get_absolute_url(), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(img.title, doc('section.media h1').text())
        eq_(img.description, doc('section.media div.description').text())
        eq_(img.file.url, doc('section.media div.media img')[0].attrib['src'])
