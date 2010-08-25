from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.test import TestCase

from nose.tools import eq_

from questions.models import Question
from upload.models import ImageAttachment
from upload.tasks import generate_thumbnail


class ImageAttachmentTestCase(TestCase):
    fixtures = ['users.json', 'questions.json']

    def setUp(self):
        super(ImageAttachmentTestCase, self).setUp()
        self.user = User.objects.all()[0]
        self.obj = Question.objects.all()[0]
        self.ct = ContentType.objects.get_for_model(self.obj)

    def tearDown(self):
        ImageAttachment.objects.all().delete()
        super(ImageAttachmentTestCase, self).tearDown()

    def test_thumbnail_or_file(self):
        """thumbnail_or_file() returns self.thumbnail if set, or else returns
        self.file"""
        image = ImageAttachment(content_object=self.obj, creator=self.user)
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            image.file.save(up_file.name, up_file, save=True)

        eq_(image.file, image.thumbnail_or_file())

        generate_thumbnail(image, up_file.name)

        eq_(image.thumbnail, image.thumbnail_or_file())
