from nose.tools import eq_

from sumo.tests import TestCase
from gallery.models import Image
from gallery.tests import image


class ImageTestCase(TestCase):

    def setUp(self):
        super(ImageTestCase, self).setUp()

    def tearDown(self):
        Image.objects.all().delete()
        super(ImageTestCase, self).tearDown()

    def test_new_image(self):
        """New Image is created and saved"""
        img = image()
        eq_('Some title', img.title)
        eq_(img.file, img.thumbnail_or_file())
        eq_(150, img.file.width)
