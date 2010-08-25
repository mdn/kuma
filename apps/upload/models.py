from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models


class ImageAttachment(models.Model):
    """An image attached to an object using a generic foreign key"""
    file = models.ImageField(upload_to=settings.IMAGE_UPLOAD_PATH)
    thumbnail = models.ImageField(upload_to=settings.THUMBNAIL_UPLOAD_PATH,
                                  null=True)
    creator = models.ForeignKey(User, related_name='image_attachments')
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()

    content_object = generic.GenericForeignKey()

    def __unicode__(self):
        return self.file.name

    def thumbnail_or_file(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail if self.thumbnail else self.file
