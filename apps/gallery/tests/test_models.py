from django.conf import settings

from nose.tools import eq_
from nose import SkipTest

from sumo.tests import TestCase
from gallery.models import Image, Video
from gallery.tests import image, video
from upload.tasks import generate_image_thumbnail


class ImageTestCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Image.objects.all().delete()
        super(ImageTestCase, self).tearDown()

    def test_new_image(self):
        """New Image is created and saved"""
        img = image()
        eq_('Some title', img.title)
        eq_(150, img.file.width)
        eq_(200, img.file.height)

    def test_thumbnail_url_if_set(self):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns self.file"""
        img = image()
        eq_(img.file.url, img.thumbnail_url_if_set())

        generate_image_thumbnail(img, img.file.name)
        eq_(img.thumbnail.url, img.thumbnail_url_if_set())


class VideoTestCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Video.objects.all().delete()
        super(VideoTestCase, self).tearDown()

    def test_new_video(self):
        """New Video is created and saved"""
        vid = video()
        eq_('Some title', vid.title)
        eq_(settings.GALLERY_VIDEO_PATH + 'test.webm', vid.webm.name)
        eq_(settings.GALLERY_VIDEO_PATH + 'test.ogv', vid.ogv.name)
        eq_(settings.GALLERY_VIDEO_PATH + 'test.flv', vid.flv.name)

    def test_thumbnail_url_if_set(self):
        """thumbnail_url_if_set() returns self.thumbnail if set, or else
        returns URL to default thumbnail"""
        # TODO: write this test when implementing video thumbnail generation
        raise SkipTest
