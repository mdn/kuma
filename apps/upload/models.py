from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models


class ImageAttachment(models.Model):
    """A tag on an item."""
    file = models.ImageField(upload_to=settings.IMAGE_UPLOAD_PATH)
    thumbnail = models.ImageField(upload_to=settings.THUMBNAIL_UPLOAD_PATH)
    creator = models.ForeignKey(User, related_name='image_attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    content_object = generic.GenericForeignKey()

    def __unicode__(self):
        return self.file.name
