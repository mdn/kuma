from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from nose.tools import eq_

from questions.models import Question
from upload.models import ImageAttachment
from upload.tasks import (_scale_dimensions, _create_thumbnail,
                          generate_thumbnail)
from upload.utils import create_image_attachment


class ScaleDimensionsTestCase(TestCase):

    def test_basic(self):
        """A square image of exact size is not scaled."""
        ts = settings.THUMBNAIL_SIZE
        (width, height) = _scale_dimensions(ts, ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_small(self):
        """A small image is not scaled."""
        ts = settings.THUMBNAIL_SIZE / 2
        (width, height) = _scale_dimensions(ts, ts)
        eq_(ts, width)
        eq_(ts, height)

    def test_width_large(self):
        """An image with large width is scaled to width=MAX."""
        ts = 120
        (width, height) = _scale_dimensions(ts * 3 + 10, ts - 1, ts)
        eq_(ts, width)
        eq_(38, height)

    def test_large_height(self):
        """An image with large height is scaled to height=MAX."""
        ts = 150
        (width, height) = _scale_dimensions(ts - 2, ts * 2 + 9, ts)
        eq_(71, width)
        eq_(ts, height)

    def test_large_both_height(self):
        """An image with both large is scaled to the largest - height."""
        ts = 150
        (width, height) = _scale_dimensions(ts * 2 + 13, ts * 5 + 30, ts)
        eq_(60, width)
        eq_(ts, height)

    def test_large_both_width(self):
        """An image with both large is scaled to the largest - width."""
        ts = 150
        (width, height) = _scale_dimensions(ts * 20 + 8, ts * 4 + 36, ts)
        eq_(ts, width)
        eq_(31, height)


class CreateThumbnailTestCase(TestCase):

    def test_basic(self):
        """A thumbnail is created from an image file."""
        # TODO: cover functionality of upload.tasks._create_thumbnail
        pass


class GenerateThumbnail(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(GenerateThumbnail, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]

    def tearDown(self):
        ImageAttachment.objects.all().delete()

    def test_basic(self):
        """generate_thumbnail overrides image thumbnail."""
        # TODO: cover functionality of upload.tasks.generate_thumbnail
