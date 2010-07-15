from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models


class ImageAttachment(models.Model):
    """A tag on an item."""
    file = models.ImageField(upload_to='uploads/images')
    thumbnail = models.ImageField(upload_to='uploads/images/thumbnails')
    creator = models.ForeignKey(User, related_name='image_attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    content_object = generic.GenericForeignKey()

    def __unicode__(self):
        return self.file.name
